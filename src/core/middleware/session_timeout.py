"""Middleware terminating authenticated sessions after inactivity."""

from __future__ import annotations

import contextlib
import re
from collections.abc import Callable
from datetime import UTC, datetime

from django.conf import settings
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import resolve_url
from django.urls import NoReverseMatch


class SessionInactivityTimeoutMiddleware:
    """Enforces server-side session termination on user inactivity."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Initialize middleware with timeout thresholds and exemptions."""
        self.get_response = get_response
        self.timeout_seconds = int(
            getattr(settings, "SESSION_INACTIVITY_TIMEOUT_SECONDS", 1800)
        )
        exempt_patterns = getattr(settings, "SESSION_INACTIVITY_EXEMPT_PATHS", [])
        self.exempt_regexes = [re.compile(p) for p in exempt_patterns]
        self.login_url = getattr(settings, "LOGIN_URL", "/users/login/")

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request and verify session activity."""
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return self.get_response(request)

        if not hasattr(request, "session"):
            return self.get_response(request)

        is_background = (
            request.headers.get("X-Background-Request", "").strip().lower() == "true"
        )
        path_matches_exempt = any(
            regex.search(request.path) for regex in self.exempt_regexes
        )

        now = datetime.now(UTC)
        last_activity_str = request.session.get("last_activity")

        if last_activity_str:
            try:
                last_activity = datetime.fromisoformat(last_activity_str)
                elapsed = (now - last_activity).total_seconds()
                if elapsed > self.timeout_seconds:
                    with contextlib.suppress(
                        KeyError, AttributeError, ValueError, RuntimeError
                    ):
                        request.session.flush()

                    try:
                        login_path = resolve_url(self.login_url)
                    except NoReverseMatch, ValueError:
                        login_path = "/auth/login/"
                    redirect_target = f"{login_path}?reason=timeout"

                    is_ajax = request.headers.get(
                        "X-Requested-With"
                    ) == "XMLHttpRequest" or "application/json" in request.headers.get(
                        "Accept", ""
                    )
                    if is_ajax:
                        return JsonResponse(
                            {
                                "error": "session_expired",
                                "redirect": redirect_target,
                            },
                            status=401,
                        )
                    return HttpResponseRedirect(redirect_target)
            except ValueError, TypeError:
                pass

        if not is_background and not path_matches_exempt:
            request.session["last_activity"] = now.isoformat()

        return self.get_response(request)
