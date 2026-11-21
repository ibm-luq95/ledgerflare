"""Authorization mixins for view-level role and permission access control."""
from __future__ import annotations

from typing import Any, ClassVar

from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext_lazy as _

from core.constants.users import (
    CON_ASSISTANT,
    CON_BOOKKEEPER,
    CON_CFO,
    CON_MANAGER,
)


class BWManagerAccessMixin(PermissionRequiredMixin):
    """Mixin restricting access to users with manager or assistant permissions."""

    permission_required: ClassVar[list[str]] = [
        "manager.manager_user",
        "assistant.assistant_user",
    ]

    def dispatch(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponse:
        """Enforce login and permission checking on dispatch."""
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        if not self.has_permission():
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def has_permission(self) -> bool:
        """Check if user has manager or assistant permission."""
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.has_perm("manager.manager_user") or user.has_perm(
            "assistant.assistant_user"
        )


class BWManagerAssistantAccessMixin(UserPassesTestMixin):
    """Mixin restricting access to managers and assistants only."""

    def test_func(self) -> bool:
        """Check if user is an authenticated manager or assistant."""
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.user_type in (CON_MANAGER, CON_ASSISTANT)


class BWObjectAccessRequiredMixin(UserPassesTestMixin):
    """Mixin enforcing object-level ownership or assignment checks for CBVs."""

    permission_denied_message: ClassVar[str] = _(
        "You do not have permission to access this record."
    )

    def test_func(self) -> bool:
        """Verify user is authorized to access the targeted object."""
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if user.user_type in (CON_MANAGER, CON_ASSISTANT):
            return True

        obj = self.get_object()

        if user.user_type == CON_BOOKKEEPER:
            if not hasattr(user, "bookkeeper"):
                return False
            bookkeeper = user.bookkeeper
            return self._check_bookkeeper_object_access(obj, bookkeeper, user)

        if user.user_type == CON_CFO:
            if not hasattr(user, "cfo"):
                return False
            cfo = user.cfo
            return self._check_cfo_object_access(obj, cfo, user)

        return False

    def _check_bookkeeper_object_access(
        self, obj: Any, bookkeeper: Any, user: Any
    ) -> bool:
        """Check if bookkeeper has access to the target object."""
        if (
            hasattr(obj, "bookkeepers")
            and obj.bookkeepers.filter(pk=bookkeeper.pk).exists()
        ):
            return True

        if (
            hasattr(obj, "client")
            and obj.client
            and hasattr(obj.client, "bookkeepers")
            and obj.client.bookkeepers.filter(pk=bookkeeper.pk).exists()
        ):
            return True

        if hasattr(obj, "bookkeeper") and obj.bookkeeper == bookkeeper:
            return True

        if hasattr(obj, "job") and obj.job:
            if hasattr(obj.job, "bookkeeper") and obj.job.bookkeeper == bookkeeper:
                return True
            if (
                hasattr(obj.job, "client")
                and obj.job.client
                and hasattr(obj.job.client, "bookkeepers")
                and obj.job.client.bookkeepers.filter(pk=bookkeeper.pk).exists()
            ):
                return True

        if hasattr(obj, "created_by") and obj.created_by == user:
            return True
        if hasattr(obj, "managed_by") and obj.managed_by == user:
            return True
        return bool(hasattr(obj, "user") and obj.user == user)

    def _check_cfo_object_access(
        self, obj: Any, cfo: Any, user: Any
    ) -> bool:
        """Check if CFO has access to the target object."""
        if hasattr(obj, "cfos") and obj.cfos.filter(pk=cfo.pk).exists():
            return True

        if (
            hasattr(obj, "client")
            and obj.client
            and hasattr(obj.client, "cfos")
            and obj.client.cfos.filter(pk=cfo.pk).exists()
        ):
            return True

        if (
            hasattr(obj, "job")
            and obj.job
            and hasattr(obj.job, "client")
            and obj.job.client
            and hasattr(obj.job.client, "cfos")
            and obj.job.client.cfos.filter(pk=cfo.pk).exists()
        ):
            return True

        if hasattr(obj, "created_by") and obj.created_by == user:
            return True
        if hasattr(obj, "managed_by") and obj.managed_by == user:
            return True
        return bool(hasattr(obj, "user") and obj.user == user)



