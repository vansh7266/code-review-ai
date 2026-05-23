from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.database import get_db
from backend.routes.auth import get_current_user
from backend.models import User, Review, ReviewComment
from backend.services.db_service import DBService

router = APIRouter()

@router.get("/history")
async def get_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetches list of code reviews submitted by the authenticated user."""
    reviews = await DBService.get_user_reviews(db, current_user.id)
    return {
        "history": [
            {
                "id": r.id,
                "repo_name": r.repo_name,
                "pr_number": r.pr_number,
                "pr_url": r.pr_url,
                "status": r.status,
                "created_at": r.created_at
            }
            for r in reviews
        ]
    }

@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetches high-level review performance statistics aggregated dynamically from the DB."""
    # Count total reviews
    reviews = await DBService.get_user_reviews(db, current_user.id)
    total_reviews = len(reviews)
    
    # Calculate comment category tallies
    bugs_found = 0
    security_issues = 0
    code_smells = 0
    
    if total_reviews > 0:
        review_ids = [r.id for r in reviews]
        query = (
            select(ReviewComment.severity, ReviewComment.category, func.count(ReviewComment.id))
            .where(ReviewComment.review_id.in_(review_ids))
            .group_by(ReviewComment.severity, ReviewComment.category)
        )
        
        result = await db.execute(query)
        for severity, category, count in result.all():
            sev_lower = severity.lower()
            cat_lower = category.lower()
            
            if sev_lower == "critical" or cat_lower == "bug":
                bugs_found += count
            elif sev_lower == "major" or cat_lower == "security":
                security_issues += count
            else:
                code_smells += count

    return {
        "total_reviews": total_reviews,
        "bugs_found": bugs_found,
        "security_issues": security_issues,
        "code_smells": code_smells
    }
