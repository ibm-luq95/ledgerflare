"""Permission classes for manager-level API access control."""
from __future__ import annotations

from typing import ClassVar

from django.http import HttpRequest
from rest_framework import permissions
from rest_framework.views import APIView

from core.choices import BeachWoodUserTypeEnum


class ManagerApiPermission(permissions.BasePermission):
    """Permission class restricting API access to managers and assistants only."""

    edit_methods: ClassVar[tuple[str, ...]] = ("PUT", "PATCH")

    def has_permission(self, request: HttpRequest, view: APIView) -> bool:
        """Check if requesting user has manager or assistant privileges."""
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        return request.user.user_type in (
            BeachWoodUserTypeEnum.MANAGER,
            BeachWoodUserTypeEnum.ASSISTANT,
        )


