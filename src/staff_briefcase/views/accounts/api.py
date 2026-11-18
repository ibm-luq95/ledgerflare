"""API ViewSets for Staff Accounts."""

from __future__ import annotations

from typing import Any, ClassVar

from django.db.models import QuerySet
from rest_framework import permissions
from rest_framework.viewsets import ModelViewSet

from core.api.mixins import RoleScopedQuerysetMixin
from core.api.permissions import BaseApiPermissionMixin
from core.choices import BeachWoodUserTypeEnum
from core.crypto.blind_index import compute_trigram_blind_index
from core.utils import get_formatted_logger
from staff_briefcase.models import StaffAccounts
from staff_briefcase.serializers import StaffAccountsSerializer


logger = get_formatted_logger()


class StaffAccountsViewSet(RoleScopedQuerysetMixin, ModelViewSet):
    """ViewSet for managing staff accounts with trigram blind index search."""

    serializer_class = StaffAccountsSerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    perm_slug = "staff_briefcase.staffaccounts"
    queryset = StaffAccounts.objects.all()
    filterset_fields: ClassVar[list[str]] = ["name", "is_deleted"]
    search_fields: ClassVar[list[str]] = ["name", "title", "username_email"]
    ordering_fields: ClassVar[list[str]] = [
        "created_at",
        "updated_at",
        "title",
        "name",
    ]
    ordering: ClassVar[list[str]] = ["title"]

    def scope_queryset_for_bookkeeper(
        self, queryset: QuerySet[StaffAccounts], bookkeeper: Any
    ) -> QuerySet[StaffAccounts]:
        """Scope queryset for bookkeepers to their briefcase accounts."""
        return queryset.filter(briefcase__user=bookkeeper.user).distinct()

    def scope_queryset_for_cfo(
        self, queryset: QuerySet[StaffAccounts], cfo: Any
    ) -> QuerySet[StaffAccounts]:
        """Scope queryset for CFO users to their briefcase accounts."""
        return queryset.filter(briefcase__user=cfo.user).distinct()

    def filter_queryset(
        self, queryset: QuerySet[StaffAccounts]
    ) -> QuerySet[StaffAccounts]:
        """Filter queryset with dual-lookup support for trigram blind indexed fields."""
        query_params = getattr(
            self.request, "query_params", getattr(self.request, "GET", {})
        )
        search_term = query_params.get("search")
        if search_term and len(search_term.strip()) >= 3:
            trigrams = compute_trigram_blind_index(
                search_term.strip(), context="staffaccounts:username_email"
            )
            standard_qs = super().filter_queryset(queryset)
            if trigrams:
                return (
                    standard_qs
                    | queryset.filter(username_email_bidx__contains=trigrams)
                ).distinct()
            return standard_qs
        return super().filter_queryset(queryset)

    def get_queryset(self) -> QuerySet[StaffAccounts]:
        """Get base queryset scoped by user role."""
        queryset = super().get_queryset()
        user = self.request.user
        if (
            user
            and user.is_authenticated
            and not user.is_superuser
            and user.user_type != BeachWoodUserTypeEnum.MANAGER
        ):
            return queryset.filter(briefcase__user=user).distinct()
        return queryset
