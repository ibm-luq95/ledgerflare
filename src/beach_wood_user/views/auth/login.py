"""beach_wood_user/auth/views.py - Secure login view with DRF token integration"""

from __future__ import annotations
from typing import Any, Dict, Optional, TypeVar, cast
from dataclasses import asdict
from datetime import datetime
from functools import lru_cache
import logging
import re
import secrets
from ipaddress import ip_address
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic.edit import FormMixin
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured

# Rest of imports remain the same
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from beach_wood_user.forms import BWLoginForm
from beach_wood_user.models import BWUser
from core.cache import BWSiteSettingsViewMixin
from core.utils.grab_env_file import grab_env_file

logger = logging.getLogger(__name__)
T = TypeVar("T")

# Rate limiting constants
FAILED_LOGIN_ATTEMPTS_LIMIT = 5
FAILED_LOGIN_TIMEOUT = 300  # seconds (5 minutes)


@method_decorator(csrf_protect, name="dispatch")
class BWLoginViewBW(SuccessMessageMixin, BWSiteSettingsViewMixin, FormMixin, View):
    """
    BWLoginViewBW Default login form view
    Customized login form for staff members with integrated DRF token support.

    Features:

    - CSRF protected login
    - Environment-specific configuration
    - DRF token generation on successful login
    - User-type aware redirection
    - Enhanced security with generic error messages
    - Rate limiting of failed attempts
    - IP-based account lockout
    - Modern type-hinted implementation following PEP 8 and Python best practices

    :ivar str template_name: Path to the login template
    :ivar BWLoginForm form_class: Form class for validation
    :ivar str success_message: Message shown on successful login
    :ivar reverse_lazy success_url: Default URL to redirect after login

    Example:

    >>> path('login/', BWLoginViewBW.as_view(), name='login')

    .. warning::
        This view requires CSRF protection which is enforced via dispatch decorator.
    """

    template_name: str = "beach_wood_user/auth/login.html"
    form_class = BWLoginForm
    success_message: str = _("Login successfully")
    success_url = reverse_lazy("auth:login")

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Handle GET requests: instantiate a blank version of the form.

        :param HttpRequest request: Incoming HTTP request
        :return: Rendered HTML response
        :rtype: HttpResponse
        """
        try:
            # Store next parameter in session if provided
            if request.GET.get("next"):
                request.session.setdefault("next", request.GET.get("next"))

            # Redirect authenticated users
            if request.user.is_authenticated:
                user_type = cast(str, request.user.user_type)  # type: ignore
                return self._get_redirect_response(user_type)

            context = self.get_context_data()
            return render(request, self.template_name, context)

        except Exception as e:
            logger.exception("GET request failed: %s", e)
            raise

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Handle POST requests with secure form processing.

        :param HttpRequest request: Incoming HTTP request
        :return: Rendered HTML response or redirect
        :rtype: HttpResponse
        """
        try:
            # Rate limiting check
            if self._is_rate_limited(request):
                logger.warning(
                    "Rate limit exceeded for IP: %s", self._get_client_ip(request)
                )
                messages.error(
                    request, _("Too many failed attempts. Please try again later.")
                )
                return self.form_invalid(self.get_form())

            form = self.get_form()

            if form.is_valid():
                return self.form_valid(form)

            return self.form_invalid(form)

        except Exception as e:
            logger.exception("POST request failed: %s", e)
            raise

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Get context data for template rendering.

        :param kwargs: Additional context parameters
        :return: Dictionary containing context data
        :rtype: dict
        """
        context = {
            "title": _("Login"),
            "AUTH_TOKEN": (
                self.request.session.get("auth_token")
                if self.request.user.is_authenticated
                else None
            ),
        }

        # Add form to context
        if "form" not in context:
            context["form"] = self.get_form()

        return context

    def get_form_kwargs(self) -> dict[str, Any]:
        """
        Return the keyword arguments to instantiate the form.

        :return: Dictionary of form initialization arguments
        :rtype: dict
        """
        kwargs = super().get_form_kwargs()
        config = grab_env_file()
        environment = config("STAGE_ENVIRONMENT", cast=str)

        logger.debug(f"Current environment: {environment}")

        # Get any existing initial data
        initial = kwargs.get("initial", {})
        logger.debug(f"Initial before update: {initial}")

        # Add environment-specific defaults
        if environment in ["DEV", "STAGE", "LOCAL_DEV"]:
            initial.setdefault("user_type", "manager")
            logger.debug(f"Initial after update: {initial}")

        # Update kwargs with merged initial data
        kwargs["initial"] = initial
        return kwargs

    def form_valid(self, form: BWLoginForm) -> HttpResponse:
        """
        Process valid form submission with secure authentication flow.

        :param BWLoginForm form: Validated form instance
        :return: Redirect response to appropriate destination
        :rtype: HttpResponse
        """
        try:
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            user_type = form.cleaned_data.get("user_type")

            # Validate user credentials
            validation_result = self._validate_credentials(email, user_type)

            if not validation_result["valid"]:
                form.add_error(None, validation_result["error"])
                self._record_failed_attempt(self.request)
                return self.form_invalid(form)

            user = validation_result["user"]

            # Authenticate user
            auth_result = self._authenticate_user(email, password)

            if not auth_result["authenticated"]:
                form.add_error(None, auth_result["error"])
                self._record_failed_attempt(self.request)
                return self.form_invalid(form)

            # Clear failed attempts on successful login
            self._clear_failed_attempts(self.request)

            # Store token and login
            self._handle_post_login(user)

            # Determine redirect
            return self._determine_redirect(user)

        except Exception as e:
            logger.exception("Form validation failed: %s", e)
            messages.error(self.request, _("Error while logging in"))
            return self.form_invalid(form)

    def form_invalid(self, form: BWLoginForm) -> HttpResponse:
        """
        Handle invalid form submission.

        :param BWLoginForm form: Invalid form instance
        :return: Rendered HTML response with errors
        :rtype: HttpResponse
        """
        context = self.get_context_data(form=form)
        return render(self.request, self.template_name, context, status=400)

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "")

        # Basic IP validation
        try:
            ip_obj = ip_address(ip)
            return str(ip_obj)
        except ValueError:
            return "unknown"

    def _get_rate_limit_key(self, request: HttpRequest) -> str:
        """Get cache key for rate limiting based on request."""
        ip = self._get_client_ip(request)
        return f"login_attempts:{ip}"

    def _is_rate_limited(self, request: HttpRequest) -> bool:
        """Check if request should be rate limited."""
        rate_limit_key = self._get_rate_limit_key(request)
        failed_attempts = cache.get(rate_limit_key, 0)
        return failed_attempts >= FAILED_LOGIN_ATTEMPTS_LIMIT

    def _record_failed_attempt(self, request: HttpRequest) -> None:
        """Record a failed login attempt."""
        rate_limit_key = self._get_rate_limit_key(request)
        failed_attempts = cache.get(rate_limit_key, 0)

        cache.set(rate_limit_key, failed_attempts + 1, timeout=FAILED_LOGIN_TIMEOUT)

        logger.info(
            "Recorded failed login attempt for IP: %s (count: %d)",
            self._get_client_ip(request),
            failed_attempts + 1,
        )

    def _clear_failed_attempts(self, request: HttpRequest) -> None:
        """Clear failed login attempts counter."""
        rate_limit_key = self._get_rate_limit_key(request)
        cache.delete(rate_limit_key)

    def _get_redirect_response(self, user_type: str) -> HttpResponseRedirect:
        """Get appropriate redirect response based on user type."""
        redirect_map = {
            "bookkeeper": "dashboard:bookkeeper:home",
            "manager": "dashboard:manager:home",
            "assistant": "dashboard:manager:home",
            "cfo": "dashboard:cfo:home",
        }

        url_name = redirect_map.get(user_type)
        if not url_name:
            raise PermissionDenied(_("Invalid user type"))

        return redirect(url_name)

    def _validate_credentials(
        self, email: str, submitted_user_type: str
    ) -> Dict[str, Any]:
        """
        Validate that the submitted credentials are valid.

        :param str email: User's email address
        :param str submitted_user_type: User type submitted in form
        :return: Dictionary with validation results
        :rtype: dict
        """
        try:
            user = BWUser.objects.get(email=email)

            if submitted_user_type != user.user_type:
                # Always use generic message in production
                return {"valid": False, "error": _("Invalid credentials"), "user": user}

            return {"valid": True, "user": user}

        except BWUser.DoesNotExist:
            return {"valid": False, "error": _("Invalid credentials")}

    def _authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Attempt to authenticate the user with given credentials.

        :param str email: User's email address
        :param str password: User's password
        :return: Dictionary with authentication results
        :rtype: dict
        """
        user = authenticate(self.request, email=email, password=password)

        if user is None:
            return {"authenticated": False, "error": _("Invalid credentials")}

        return {"authenticated": True, "user": user}

    def _handle_post_login(self, user: BWUser) -> None:
        """
        Handle post-login operations including token generation.

        :param BWUser user: Authenticated user instance
        """
        # Generate or get existing DRF token
        token, created = Token.objects.get_or_create(user=user)

        # Store token in session for frontend access
        self.request.session["auth_token"] = token.key
        self.request.session.modified = True

        # Actual login
        login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")

    def _determine_redirect(self, user: BWUser) -> HttpResponseRedirect:
        """
        Determine where to redirect after successful login.

        :param BWUser user: Authenticated user instance
        :return: Redirect response to appropriate destination
        :rtype: HttpResponseRedirect
        """
        # Check next URL from session
        next_url = self.request.session.get("next")
        if next_url:
            del self.request.session["next"]
            return redirect(next_url)

        # Fallback to user type-based redirect
        redirect_map = {
            "bookkeeper": "dashboard:bookkeeper:home",
            "manager": "dashboard:manager:home",
            "assistant": "dashboard:manager:home",
            "cfo": "dashboard:cfo:home",
        }

        user_type = cast(str, user.user_type)  # type: ignore
        url_name = redirect_map.get(user_type)

        if not url_name:
            raise PermissionDenied(_("Invalid user type"))

        return redirect(url_name)
