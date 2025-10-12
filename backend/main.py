"""Main FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.database import init_db
from app.init_db import initialize_database
from app.api import requests as requests_router
from app.api import commodity_groups as commodity_groups_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    # Create uploads directory if it doesn't exist
    settings.upload_dir.mkdir(parents=True, exist_ok=True)

    # Initialize database tables and seed data
    initialize_database()

    yield

    # Cleanup can go here if needed


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for managing procurement requests with PDF extraction and AI-powered classification",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for serving PDFs
uploads_path = Path(__file__).parent / "app" / "uploads"
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

# Include API routers
app.include_router(
    requests_router.router,
    prefix=f"{settings.api_prefix}/requests",
    tags=["requests"]
)
app.include_router(
    commodity_groups_router.router,
    prefix=f"{settings.api_prefix}/commodity-groups",
    tags=["commodity-groups"]
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Procurement Request System API",
        "version": settings.app_version,
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
