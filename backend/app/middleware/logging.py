"""Request logging middleware for FastAPI.

This module provides HTTP request/response logging middleware with timing
information for monitoring and debugging.
"""

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.logger import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming HTTP requests with timing information.

    Captures request details, response status, and execution duration for
    all HTTP requests passing through the application.
    """

    async def dispatch(self, request: Request, call_next):
        """Process and log HTTP request/response cycle.

        Args:
            request (Request): The incoming HTTP request.
            call_next: Callable to process the request.

        Returns:
            Response: The HTTP response from the application.

        Raises:
            Exception: Re-raises any exception that occurs during processing.
        """
        # Start timer
        start_time = time.time()

        # Log incoming request
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"from {request.client.host}"
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"status={response.status_code} duration={duration:.3f}s"
            )

            return response
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"error={str(e)} duration={duration:.3f}s",
                exc_info=True
            )
            raise
