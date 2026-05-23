import os
from pathlib import Path
from dotenv import load_dotenv

# Locate and load the .env file from the root directory
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    """Type-annotated configuration class that handles loading keys from environment variables."""
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "your_github_client_id")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "your_github_client_secret")
    GITHUB_REDIRECT_URI: str = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/auth/callback")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "your_gemini_api_key")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "mysecretkey123")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./code_review.db")

# Instantiate settings to be imported by other modules
settings = Settings()

import jwt
import datetime
from fastapi import HTTPException, status

def create_jwt(user_id: int) -> str:
    """Creates a cryptographically signed JWT token for the specified user_id with a 24-hour expiration."""
    payload = {
        "sub": str(user_id),
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def decode_jwt(token: str) -> int:
    """Decodes and validates a signed JWT token, returning the user_id or raising an error on failure."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise jwt.InvalidTokenError("Token payload missing subject field.")
        return int(user_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please authenticate again."
        )
    except jwt.InvalidTokenError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid session credentials: {str(err)}"
        )
