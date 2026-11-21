"""API view for dynamically resolving URL paths by name."""

from __future__ import annotations

from typing import Any

from django.urls import reverse_lazy
from django.urls.exceptions import NoReverseMatch
from rest_framework import permissions, status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.exceptions import APIException
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.utils import get_formatted_logger


logger = get_formatted_logger()


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """Session authentication bypassing CSRF checks for read-only utility endpoints."""

    def enforce_csrf(self, request: Request) -> None:
        """Bypass CSRF enforcement for stateless, read-only URL resolution."""
        return


class FetchUrlApiView(APIView):
    """API view for dynamically resolving URL paths by name.

    Permissions:
        IsAuthenticated: Authenticated users only.
    """

    authentication_classes = (CsrfExemptSessionAuthentication, TokenAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Resolve a URL path via HTTP GET query parameters."""
        url_name = request.query_params.get("urlName")
        if not url_name:
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "user_error_msg": "urlName query parameter is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        pk = request.query_params.get("pk")
        try:
            if pk is not None:
                url_path = reverse_lazy(url_name, kwargs={"pk": pk})
            else:
                url_path = reverse_lazy(url_name)
            return Response(
                {"urlPath": str(url_path)},
                status=status.HTTP_200_OK,
            )
        except (NoReverseMatch, APIException) as ex:
            logger.exception("Failed to reverse URL name: %s", url_name)
            detail = getattr(ex, "default_detail", str(ex))
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "user_error_msg": detail,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as ex:
            logger.exception("Unexpected error while resolving URL path")
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "error": str(ex),
                    "user_error_msg": "Error while fetching URL path!",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Resolve a URL path via HTTP POST body payload."""
        data = request.data or {}
        url_name = data.get("urlName")
        if not url_name:
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "user_error_msg": "urlName is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        pk = data.get("pk")
        try:
            if pk is not None:
                url_path = reverse_lazy(url_name, kwargs={"pk": pk})
            else:
                url_path = reverse_lazy(url_name)
            return Response(
                {"urlPath": str(url_path)},
                status=status.HTTP_200_OK,
            )
        except (NoReverseMatch, APIException) as ex:
            logger.exception("Failed to reverse URL name: %s", url_name)
            detail = getattr(ex, "default_detail", str(ex))
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "user_error_msg": detail,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as ex:
            logger.exception("Unexpected error while resolving URL path")
            return Response(
                {
                    "status": status.HTTP_400_BAD_REQUEST,
                    "error": str(ex),
                    "user_error_msg": "Error while fetching URL path!",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
