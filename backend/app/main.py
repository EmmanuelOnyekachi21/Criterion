"""FastAPI application factory and router configuration.

This module initializes the FastAPI application with lifespan management
for database setup/teardown and includes all API routers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import admin, analyses, health, webhooks
from app.database import Base, engine
from app.logger import logger
from app.middleware.logging import RequestLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events.

    On startup: Logs application start.
    On shutdown: Disposes of the database engine.

    Note: Database migrations are handled by Alembic, not at startup.
    Run 'alembic upgrade head' to apply migrations.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None: Control returns to FastAPI during the running phase.
    """
    # Startup
    logger.info("Criterion starting up!")

    # Database tables are managed by Alembic migrations
    # Run: alembic upgrade head
    yield
    # Runs on shutdown
    await engine.dispose()
    logger.info("Criterion shutting down")


app = FastAPI(
    title="Criterion",
    description="GitLab MR analysis agent",
    version="0.1.0",
    lifespan=lifespan
)

logger.info("FastAPI application initialized")

# Add middlewares
app.add_middleware(RequestLoggingMiddleware)

app.include_router(webhooks.router, prefix="/api/webhooks")
# app.include_router(analyses.router, prefix="/api/analyses")
app.include_router(admin.router, prefix="/api")
app.include_router(health.router)
