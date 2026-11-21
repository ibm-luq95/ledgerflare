# -*- coding: utf-8 -*-#

from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.viewsets import ModelViewSet

from core.api.mixins import RoleScopedQuerysetMixin
from core.api.permissions import BaseApiPermissionMixin
from core.utils import get_formatted_logger
from staff_briefcase.models import StaffNotes
from staff_briefcase.serializers import StaffNotesSerializer

logger = get_formatted_logger()


class StaffNotesViewSet(RoleScopedQuerysetMixin, ModelViewSet):
    serializer_class = StaffNotesSerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    perm_slug = "staff_briefcase.staffnotes"
    queryset = StaffNotes.objects.all()
    filterset_fields = ["is_deleted"]
    search_fields = ["title", "note"]
    ordering_fields = ["created_at", "updated_at", "title"]
    ordering = ["-created_at"]

    def scope_queryset_for_bookkeeper(self, queryset, bookkeeper):
        return queryset.filter(briefcase__user=bookkeeper.user).distinct()

    def scope_queryset_for_cfo(self, queryset, cfo):
        return queryset.filter(briefcase__user=cfo.user).distinct()

