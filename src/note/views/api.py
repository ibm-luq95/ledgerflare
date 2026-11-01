from django.db import models
from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.viewsets import ModelViewSet

from core.api.mixins import RoleScopedQuerysetMixin
from core.api.permissions import BaseApiPermissionMixin
from core.utils import get_formatted_logger
from note.models import Note
from note.serializers import NoteSerializer


logger = get_formatted_logger()


class NoteViewSet(RoleScopedQuerysetMixin, ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    perm_slug = "note.note"
    queryset = Note.objects.all()
    filterset_fields = ["note_type", "client", "job", "is_deleted"]
    search_fields = ["title", "body"]
    ordering_fields = ["created_at", "updated_at", "title"]
    ordering = ["-created_at"]

    def scope_queryset_for_bookkeeper(self, queryset, bookkeeper):
        return queryset.filter(
            models.Q(client__bookkeepers=bookkeeper) |
            models.Q(job__managed_by=bookkeeper.user) |
            models.Q(job__client__bookkeepers=bookkeeper) |
            models.Q(task__job__managed_by=bookkeeper.user) |
            models.Q(task__job__client__bookkeepers=bookkeeper)
        ).distinct()

    def scope_queryset_for_cfo(self, queryset, cfo):
        return queryset.filter(
            models.Q(client__cfos=cfo) |
            models.Q(job__client__cfos=cfo) |
            models.Q(task__job__client__cfos=cfo)
        )
