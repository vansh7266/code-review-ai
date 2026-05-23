from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.models import User, Review, ReviewComment
from typing import List, Optional

class DBService:
    """Service class containing standard helper methods to interact with SQLite via SQLAlchemy async session."""

    @staticmethod
    async def get_user_by_github_id(db: AsyncSession, github_id: str) -> Optional[User]:
        """Queries and returns a User record matching the specific github_id."""
        query = select(User).where(User.github_id == github_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create_user(db: AsyncSession, github_user_data: dict, access_token: str) -> User:
        """Upserts a User record: inserts a new record or updates access_token/profile if they already exist."""
        github_id = str(github_user_data.get("id"))
        username = github_user_data.get("login", "")
        avatar_url = github_user_data.get("avatar_url")

        # Check if user already exists
        query = select(User).where(User.github_id == github_id)
        result = await db.execute(query)
        db_user = result.scalar_one_or_none()

        if db_user:
            # Update attributes to keep in sync with GitHub
            db_user.username = username
            db_user.avatar_url = avatar_url
            db_user.access_token = access_token
        else:
            # Create new user record
            db_user = User(
                github_id=github_id,
                username=username,
                avatar_url=avatar_url,
                access_token=access_token
            )
            db.add(db_user)

        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def create_user(db: AsyncSession, github_id: str, username: str, 
                          avatar_url: Optional[str], access_token: str) -> User:
        """Saves a new User record into the database."""
        db_user = User(
            github_id=github_id,
            username=username,
            avatar_url=avatar_url,
            access_token=access_token
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def get_reviews_by_user(db: AsyncSession, user_id: int) -> List[Review]:
        """Retrieves all past review operations initialized by a specific user_id."""
        query = select(Review).where(Review.user_id == user_id).order_by(Review.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_user_reviews(db: AsyncSession, user_id: int) -> List[Review]:
        """Fetches all reviews requested by a specific user_id, ordered by creation date desc."""
        query = select(Review).where(Review.user_id == user_id).order_by(Review.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def create_review(db: AsyncSession, user_id: int, pr_url: str, 
                            repo_name: str, pr_number: int) -> Review:
        """Saves a new PR Review record into the database with a pending status."""
        db_review = Review(
            user_id=user_id,
            pr_url=pr_url,
            repo_name=repo_name,
            pr_number=pr_number,
            status="pending"
        )
        db.add(db_review)
        await db.commit()
        await db.refresh(db_review)
        return db_review

    @staticmethod
    async def add_review_comments(db: AsyncSession, review_id: int, comments: List[dict]):
        """Inserts a list of raw Gemini code comments into the review_comments database."""
        db_comments = [
            ReviewComment(
                review_id=review_id,
                file_path=item.get("file_path", "unknown"),
                line_number=item.get("line_number"),
                severity=item.get("severity", "minor"),
                category=item.get("category", "style"),
                comment=item.get("comment", "")
            )
            for item in comments
        ]
        db.add_all(db_comments)
        await db.commit()

    @staticmethod
    async def save_comments(db: AsyncSession, review_id: int, comments_list: List[dict]):
        """Bulk inserts review comments linked to a specific review_id."""
        db_comments = [
            ReviewComment(
                review_id=review_id,
                file_path=item.get("file_path", "unknown"),
                line_number=item.get("line_number"),
                severity=item.get("severity", "minor"),
                category=item.get("category", "style"),
                comment=item.get("comment", "")
            )
            for item in comments_list
        ]
        db.add_all(db_comments)
        await db.commit()

    @staticmethod
    async def get_review_detail(db: AsyncSession, review_id: int) -> Optional[Review]:
        """Fetches a Review record by ID along with all its related ReviewComments pre-loaded."""
        query = select(Review).where(Review.id == review_id).options(selectinload(Review.comments))
        result = await db.execute(query)
        return result.scalar_one_or_none()
