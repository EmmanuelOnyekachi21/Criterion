"""Configuration management using Pydantic settings.

This module defines the application settings loaded from environment variables
via the .env file.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings.

    Attributes:
        database_url (str): SQLAlchemy async database connection URL.
        redis_url (str): Redis connection URL for caching and task broker.
        gitlab_webhook_secret (str): Secret token for GitLab webhook verification.
        gitlab_token (str): GitLab API token for authentication.
        anthropic_api_key (str): API key for Anthropic Claude integration.
    """

    database_url: str
    redis_url: str
    gitlab_webhook_secret: str
    gitlab_token: str
    anthropic_api_key: str

    class Config:
        """Pydantic configuration."""

        env_file = ".env"


settings = Settings()