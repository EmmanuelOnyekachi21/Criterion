"""Database configuration and session management for async SQLAlchemy.

This module provides database engine setup, session factory, and FastAPI
dependency injection for database sessions with automatic commit/rollback.
"""

from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Database engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    future=True,
    # SQLAlchemy keeps 10 persistent database connections open and reuses them
    pool_size=10,
    max_overflow=20,
    echo=False,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for FastAPI dependency injection.

    Yields a database session with automatic commit on success and
    automatic rollback on exception.

    Yields:
        AsyncSession: An async SQLAlchemy session.

    Raises:
        Exception: Re-raises any exception that occurs during the session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Auto commit if no exception
        except Exception:
            await session.rollback()  # Auto-rollback on any error
            raise