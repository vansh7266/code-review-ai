from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from backend.config import settings

# Create async database engine for SQLite
# aiosqlite driver is used for full async support
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True for debugging SQL queries
    connect_args={"check_same_thread": False}  # Required for SQLite multi-thread access
)

# Async sessionmaker factory
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for all declarative models
class Base(DeclarativeBase):
    pass

# Dependency generator to obtain an async db session in route endpoints
async def get_db():
    """Dependency generator that yields an active async SQLAlchemy database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Database initializer to create all tables (invoked at app lifespan startup)
async def init_db():
    """Creates all defined database tables asynchronously if they do not exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
