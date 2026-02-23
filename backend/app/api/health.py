"""Health check endpoint for system status monitoring.

This module provides a health check endpoint that verifies the status of
critical services: database, Redis, and Celery workers.
"""

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.config import settings
from app.database import get_db

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check the health status of all system components.

    Verifies database connectivity, Redis availability, and Celery worker
    status. Returns 200 if all systems are healthy, 503 if any are degraded.

    Args:
        db (AsyncSession): Database session from dependency injection.

    Returns:
        JSONResponse: Status object with overall health and individual checks.
            - status: "healthy" or "degraded"
            - checks: Dictionary with status of database, redis, celery_workers
    """
    overall = "healthy"
    checks = {}

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        checks['database'] = "ok"
    except Exception:
        checks['database'] = "error"
        overall = "degraded"

    # Check Redis
    try:
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        checks['redis'] = "ok"
    except Exception:
        checks['redis'] = "error"
        overall = "degraded"

    # Check Celery workers
    try:
        workers = celery_app.control.ping(timeout=2)
        checks['celery_workers'] = "ok" if workers else "no_workers"
    except Exception:
        checks["celery_workers"] = "error"
        overall = "degraded"

    status_code = 200 if overall == "healthy" else 503

    return JSONResponse(
        status_code=status_code,
        content={
            'status': overall,
            "checks": checks
        }
    )
