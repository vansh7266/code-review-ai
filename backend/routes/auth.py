from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.future import select

from backend.database import get_db
from backend.config import settings, create_jwt, decode_jwt
from backend.services.github_service import GitHubService
from backend.services.db_service import DBService
from backend.models import User

router = APIRouter()
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency that decodes the bearer JWT token and retrieves the authenticated User from the database."""
    token = credentials.credentials
    user_id = decode_jwt(token)
    
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in system registers."
        )
    return user

@router.get("/login")
async def login():
    """Redirects the client to the GitHub OAuth authorization page to request user and repo scopes."""
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        f"&scope=user,repo"
    )
    return RedirectResponse(url=github_auth_url)

@router.get("/callback")
async def callback(code: str, db: AsyncSession = Depends(get_db)):
    """Handles the GitHub OAuth callback, exchanges code for access token, fetches profile, saves user, and issues a session JWT."""
    try:
        # 1. Exchange authorization code for access token
        access_token = await GitHubService.get_access_token(code)
        
        # 2. Retrieve GitHub profile info
        github_user_data = await GitHubService.get_user_info(access_token)
        
        # 3. Upsert user inside SQLite DB
        user = await DBService.get_or_create_user(db, github_user_data, access_token)
        
        # 4. Generate system cryptographic JWT
        jwt_token = create_jwt(user.id)
        
        # 5. Redirect browser back to dashboard passing the JWT token as parameter
        return RedirectResponse(url=f"/dashboard?token={jwt_token}")
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"GitHub OAuth Callback authentication failed: {str(err)}"
        )

@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    """Returns the profile info of the currently logged-in user."""
    return {
        "id": current_user.id,
        "github_id": current_user.github_id,
        "username": current_user.username,
        "avatar_url": current_user.avatar_url,
        "created_at": current_user.created_at
    }

@router.post("/logout")
async def logout():
    """Logs out the active user and clears the session session."""
    return {"message": "Logged out successfully from session."}
