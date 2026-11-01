# -*- coding: utf-8 -*-#

from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.viewsets import ModelViewSet

from core.api.mixins import RoleScopedQuerysetMixin
from core.api.permissions import BaseApiPermissionMixin
from core.choices import BeachWoodUserTypeEnum
from core.utils import get_formatted_logger
from staff_briefcase.models import StaffAccounts
from staff_briefcase.serializers import StaffAccountsSerializer

logger = get_formatted_logger()


class StaffAccountsViewSet(RoleScopedQuerysetMixin, ModelViewSet):
    serializer_class = StaffAccountsSerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    perm_slug = "staff_briefcase.staffaccounts"
    queryset = StaffAccounts.objects.all()
    filterset_fields = ["name", "is_deleted"]
    search_fields = ["name", "title", "username_email"]
    ordering_fields = ["created_at", "updated_at", "title", "name"]
    ordering = ["title"]

    def scope_queryset_for_bookkeeper(self, queryset, bookkeeper):
        return queryset.filter(briefcase__user=bookkeeper.user).distinct()

    def scope_queryset_for_cfo(self, queryset, cfo):
        return queryset.filter(briefcase__user=cfo.user).distinct()

    def get_queryset(self):
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
