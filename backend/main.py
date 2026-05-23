from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.database import init_db
from backend.routes.auth import router as auth_router
from backend.routes.review import router as review_router
from backend.routes.dashboard import router as dashboard_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager to run tasks on application startup and shutdown."""
    # Ensure SQLite tables exist before serving traffic
    await init_db()
    yield

app = FastAPI(
    title="AI-Powered Code Review Assistant API",
    description="Full async backend engine utilizing SQLite and Google Gemini 1.5 Flash for pull request static code audits.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend client interactions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production configurations
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules under their respective prefixes
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(review_router, prefix="/review", tags=["Code Reviews"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["Developer Dashboard"])

# Resolve target frontend static directory
frontend_path = Path(__file__).resolve().parent.parent / "frontend"

# Mount the static directory to serve HTML/CSS/JS assets
# We will mount it under "/static" to avoid clashes with main server endpoints.
app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

@app.get("/")
async def read_index():
    """Serves the index landing page directly from root."""
    from fastapi.responses import FileResponse
    return FileResponse(frontend_path / "index.html")

@app.get("/dashboard")
async def read_dashboard():
    """Serves the dashboard history view."""
    from fastapi.responses import FileResponse
    return FileResponse(frontend_path / "dashboard.html")

@app.get("/review")
async def read_review():
    """Serves the PR analysis detail inspector."""
    from fastapi.responses import FileResponse
    return FileResponse(frontend_path / "review.html")
