import logging
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import sentry_sdk

logger = logging.getLogger(__name__)


def error_500(request, exception=None):
    """
    Custom 500 error handler that:
    - Logs the error
    - Captures Sentry event ID if available
    - Provides contextual information to template
    - Handles API vs HTML responses

    Args:
        request: HttpRequest object
        exception: The exception that triggered the error (optional)

    Returns:
        HttpResponse with 500 status
    """
    # Log the error
    error_message = str(exception) if exception else "Unknown server error"
    logger.error(f"500 Error: {error_message}")

    # Prepare context
    context = {
        "error_message": error_message,
        "sentry_event_id": (
            sentry_sdk.last_event_id() if sentry_sdk.Hub.current.client else None
        ),
        "status_code": 500,
    }

    # Handle API requests differently
    if request.path.startswith("/api/"):
        return JsonResponse(
            {
                "error": "Internal Server Error",
                "message": error_message,
                "status_code": 500,
                "event_id": context["sentry_event_id"],
            },
            status=500,
        )

    return render(request, "core/errors/500.html", context, status=500)
