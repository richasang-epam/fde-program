"""
API middleware for authentication, logging, and error handling.
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time
import uuid

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())

        # Log request
        start_time = time.time()
        logger.info(f"[{request_id}] {request.method} {request.url} - Started")

        try:
            # Process request
            response = await call_next(request)

            # Log response
            process_time = time.time() - start_time
            logger.info(
                f"[{request_id}] {request.method} {request.url} - "
                f"Completed in {process_time:.3f}s - Status: {response.status_code}"
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                f"[{request_id}] {request.method} {request.url} - "
                f"Error in {process_time:.3f}s: {str(e)}"
            )
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for standardized error handling."""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response

        except HTTPException as e:
            # Re-raise HTTP exceptions as-is
            raise

        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)

            # Return standardized error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred. Please try again later.",
                    "request_id": getattr(request.state, 'request_id', 'unknown')
                }
            )


# Authentication middleware would go here in a production system
# For now, we'll use query parameters for simplicity

class AuthMiddleware(BaseHTTPMiddleware):
    """Simple authentication middleware using query parameters."""

    async def dispatch(self, request: Request, call_next):
        # In production, this would validate JWT tokens, API keys, etc.
        # For now, we'll just ensure required parameters are present for protected endpoints

        if request.url.path.startswith("/api/v1"):
            # Check for user_role parameter on API endpoints
            user_role = request.query_params.get("user_role")
            if not user_role:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Authentication required", "message": "user_role parameter missing"}
                )

        response = await call_next(request)
        return response