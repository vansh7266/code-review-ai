import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.database import get_db
from backend.routes.auth import get_current_user
from backend.models import User, Review
from backend.services.db_service import DBService
from backend.services.github_service import GitHubService
from backend.services.gemini_service import GeminiService

router = APIRouter()

@router.post("/analyze")
async def analyze_pr(
    pr_url: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Triggers analysis on a given GitHub PR URL: fetches the diff, sends it to Gemini, saves review feedback, and posts comments."""
    review = None
    try:
        # 1. Parse pr_url to extract owner, repo, and pr_number using regex
        match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
        if not match:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid GitHub Pull Request URL. Must match: https://github.com/owner/repo/pull/num"
            )
        owner, repo, pr_number = match.groups()
        repo_full_name = f"{owner}/{repo}"
        
        # 2. Call GitHubService to retrieve the raw branch diff
        diff_text = await GitHubService.get_pr_diff(pr_url, current_user.access_token)
        
        # 3. Create a pending review record inside the SQLite DB
        review = await DBService.create_review(db, current_user.id, pr_url, repo_full_name, int(pr_number))
        
        # 4. Instantiate GeminiService and run code analysis on the diff
        gemini_service = GeminiService()
        comments = await gemini_service.analyze_diff(diff_text)
        
        # 5. Save generated comments to the review_comments database
        await DBService.save_comments(db, review.id, comments)
        
        # 6. Fetch review by ID and update status to "completed" in SQLAlchemy session
        res = await db.execute(select(Review).where(Review.id == review.id))
        db_review = res.scalar_one()
        db_review.status = "completed"
        await db.commit()
        
        # 7. Aggregate counts by severity to write the review summary comment
        critical_count = sum(1 for c in comments if c.get("severity", "").lower() == "critical")
        major_count = sum(1 for c in comments if c.get("severity", "").lower() == "major")
        minor_count = sum(1 for c in comments if c.get("severity", "").lower() == "minor")
        info_count = sum(1 for c in comments if c.get("severity", "").lower() == "info")

        summary_body = (
            f"## ReviewAI Summary\n\nFound {len(comments)} issues:\n"
            f"- Critical: {critical_count}\n"
            f"- Major: {major_count}\n"
            f"- Minor: {minor_count}\n"
            f"- Info: {info_count}"
        )
        
        # 8. Post general summary review comment back to the GitHub PR
        try:
            await GitHubService.post_review_comment(repo_full_name, int(pr_number), summary_body, current_user.access_token)
        except Exception as gh_err:
            # We don't fail the API call if posting back to GitHub fails
            print(f"Failed to post summary review comment to GitHub PR: {str(gh_err)}")
            
        return {
            "status": "completed",
            "review_id": review.id,
            "total_issues": len(comments)
        }
    except Exception as err:
        # If the review record was created before the crash, update its status to failed
        if review:
            try:
                res = await db.execute(select(Review).where(Review.id == review.id))
                db_review = res.scalar_one_or_none()
                if db_review:
                    db_review.status = "failed"
                    await db.commit()
            except Exception as db_err:
                print(f"Failed to set review status to failed: {str(db_err)}")
                
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PR Analysis failed: {str(err)}"
        )

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
