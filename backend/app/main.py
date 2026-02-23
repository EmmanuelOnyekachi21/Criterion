"""FastAPI application factory and router configuration.

This module initializes the FastAPI application with lifespan management
for database setup/teardown and includes all API routers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import analyses, health, webhooks
from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events.

    On startup: Creates all database tables.
    On shutdown: Disposes of the database engine.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None: Control returns to FastAPI during the running phase.
    """
    # Startup
    print("Criterion starting up!")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Runs on shutdown
    await engine.dispose()
    print("Criterion shutting down")


app = FastAPI(
    title="Criterion",
    description="GitLab MR analysis agent",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(webhooks.router, prefix="/webhooks")
# app.include_router(analyses.router, prefix="/analyses")
app.include_router(health.router)
