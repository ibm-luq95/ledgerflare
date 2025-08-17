import logging
from urllib.parse import urlparse
from django.http import JsonResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)

# Define excluded paths at module level
EXCLUDED_404_PATHS = [
    "/favicon.ico",
    "/robots.txt",
    "/apple-touch-icon.png",
    "/static/",
    "/media/",
    "/admin/",
    "/ads.txt",
    "/.well-known/",
    "/browserconfig.xml",
    "/site.webmanifest",
    "/sitemap.xml",
    "/.env",
]


def normalize_path(path):
    """Normalize path for consistent comparison"""
    return urlparse(path).path.rstrip("/")


def error_404(request, exception):
    """
    Enhanced 404 error handler that:
    - Logs missing paths (excluding common noise paths)
    - Provides detailed context to templates
    - Handles API and HTML responses differently
    - Identifies model-not-found scenarios
    - Normalizes paths for accurate matching

    Args:
        request: HttpRequest object
        exception: The exception that triggered the 404

    Returns:
        HttpResponse with 404 status and appropriate content type
    """
    requested_path = normalize_path(request.path)
    error_message = str(exception) if exception else "Page not found"

    # Check if path should be excluded from logging
    should_log = not any(
        requested_path == normalize_path(p)
        or requested_path.startswith(normalize_path(p) + "/")
        for p in EXCLUDED_404_PATHS
    )

    if should_log:
        logger.warning(
            f"404 Not Found - Path: {requested_path}, "
            f"Referrer: {request.META.get('HTTP_REFERER', 'none')}, "
            f"User Agent: {request.META.get('HTTP_USER_AGENT', 'unknown')}"
        )

    # Prepare context with additional diagnostic info
    context = {
        "requested_path": requested_path,
        "error_message": error_message,
        "status_code": 404,
        "is_model_not_found": getattr(exception, "model", None) is not None,
        "missing_model": (
            getattr(exception, "model", None).__name__
            if getattr(exception, "model", None)
            else None
        ),
        "referrer": request.META.get("HTTP_REFERER"),
    }

    # Handle API requests with JSON response
    if request.path.startswith("/api/"):
        return JsonResponse(
            {
                "error": "Not Found",
                "path": requested_path,
                "message": error_message,
                "status_code": 404,
                "model": context["missing_model"],
                "documentation_url": "",
            },
            status=404,
        )

    # Standard HTML response
    return render(request, "core/errors/404.html", context, status=404)
