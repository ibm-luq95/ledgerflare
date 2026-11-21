"""API view for securely revealing staff account credentials on demand."""

from __future__ import annotations

import logging
from typing import Any

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.throttling import AuthEndpointRateThrottle
from core.constants.users import CON_MANAGER
from staff_briefcase.models import StaffAccounts


logger = logging.getLogger("security")


class StaffAccountRevealPasswordApiView(APIView):
    """Secure endpoint for on-demand decryption of staff briefcase credentials."""

    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = (AuthEndpointRateThrottle,)
    http_method_names = ("post",)

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Decrypt and return staff account password with audit logging."""
        pk = kwargs.get("pk")
        account = get_object_or_404(StaffAccounts, pk=pk)
        user = request.user

        # Access check: owner of briefcase or manager/superuser
        if (
            not user.is_superuser
            and user.user_type != CON_MANAGER
            and not account.briefcase.filter(user=user).exists()
        ):
            return Response(
                {
                    "detail": (
                        "You do not have permission to view credentials for this"
                        " account."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        logger.info(
            "User %s revealed credentials for StaffAccount %s",
            user.pk,
            account.pk,
        )

        return Response(
            {
                "password": account.decrypted_password,
                "status": "success",
            },
            status=status.HTTP_200_OK,
        )
