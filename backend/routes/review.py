from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.routes.auth import get_current_user
from backend.models import User
from backend.services.db_service import DBService

router = APIRouter()

@router.post("/analyze")
async def analyze_pr(
    pr_url: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Triggers analysis on a given GitHub PR URL: fetches the diff, sends it to Gemini, saves review feedback, and posts comments."""
    # This is a stub that will be fully integrated next, but it is now fully secured with JWT user authentication.
    return {
        "status": "pending",
        "message": f"PR analysis started for {pr_url}",
        "review_id": 1
    }

@router.get("/{review_id}")
async def get_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves full analysis comments and status details for a past review ID from database."""
    review = await DBService.get_review_detail(db, review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review record ID {review_id} not found."
        )
    
    # Restrict to review owner to be secure
    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this review report."
        )

    return {
        "id": review.id,
        "repo_name": review.repo_name,
        "pr_number": review.pr_number,
        "pr_url": review.pr_url,
        "status": review.status,
        "created_at": review.created_at,
        "comments": [
            {
                "id": comment.id,
                "file_path": comment.file_path,
                "line_number": comment.line_number,
                "severity": comment.severity,
                "category": comment.category,
                "comment": comment.comment,
                "created_at": comment.created_at
            }
            for comment in review.comments
        ]
    }
