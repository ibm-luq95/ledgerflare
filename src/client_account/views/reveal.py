"""API view for securely revealing decrypted client account passwords on demand."""

from __future__ import annotations

import logging
from typing import Any

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from client_account.models import ClientAccountProxy
from core.api.throttling import AuthEndpointRateThrottle
from core.constants.users import CON_BOOKKEEPER, CON_CFO, CON_MANAGER


logger = logging.getLogger("security")


class ClientAccountRevealPasswordApiView(APIView):
    """Secure endpoint for on-demand decryption of client account passwords."""

    permission_classes = (permissions.IsAuthenticated,)
    throttle_classes = (AuthEndpointRateThrottle,)
    http_method_names = ("post",)

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Decrypt and return account password with audit logging."""
        pk = kwargs.get("pk")
        account = get_object_or_404(ClientAccountProxy, pk=pk)
        user = request.user

        # Object-level permission check
        if not user.is_superuser and user.user_type != CON_MANAGER:
            client = account.client
            if not client:
                return Response(
                    {"detail": "Account has no associated client."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            if user.user_type == CON_BOOKKEEPER:
                if not (
                    hasattr(user, "bookkeeper")
                    and client.bookkeepers.filter(pk=user.bookkeeper.pk).exists()
                ):
                    return Response(
                        {
                            "detail": (
                                "You do not have permission to view credentials"
                                " for this client."
                            )
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
            elif user.user_type == CON_CFO:
                if not (
                    hasattr(user, "cfo") and client.cfos.filter(pk=user.cfo.pk).exists()
                ):
                    return Response(
                        {
                            "detail": (
                                "You do not have permission to view credentials"
                                " for this client."
                            )
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
            else:
                return Response(
                    {"detail": "You do not have permission to view credentials."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Audit access
        logger.info(
            "User %s revealed credentials for ClientAccount %s (Client %s)",
            user.pk,
            account.pk,
            account.client_id,
        )

        return Response(
            {
                "password": account.decrypted_account_password,
                "status": "success",
            },
            status=status.HTTP_200_OK,
        )
