"""Configuration management using Pydantic settings.

This module defines the application settings loaded from environment variables
via the .env file.
"""

from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings.

    Attributes:
        database_url (str): SQLAlchemy async database connection URL.
        redis_url (str): Redis connection URL for caching and task broker.
        gitlab_webhook_secret (str): Secret token for GitLab webhook
            verification.
        gitlab_token (str): GitLab API token for authentication.
        gitlab_url (str): GitLab instance URL.
        anthropic_api_key (str): API key for Anthropic Claude integration.
        log_level (str): Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL).
        log_to_file (bool): Whether to enable file logging.
        log_file_path (str): Path to log file.
        log_file_max_bytes (int): Maximum log file size before rotation.
        log_file_backup_count (int): Number of rotated log files to keep.
        log_format (str): Log message format string.
    """

    database_url: str
    redis_url: str
    gitlab_webhook_secret: str
    gitlab_token: str
    gitlab_url: str
    anthropic_api_key: str

    # Logging configuration
    log_level: Literal[
        "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    ] = "INFO"
    log_to_file: bool = True
    log_file_path: str = "logs/app.log"
    log_file_max_bytes: int = 10 * 1024 * 1024  # 10MB
    log_file_backup_count: int = 5  # Keep 5 rotated files
    log_format: str = (
        "%(asctime)s | %(levelname)-8s | "
        "%(name)s:%(funcName)s:%(lineno)d | %(message)s"
    )

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        case_sensitive = False


settings = Settings()