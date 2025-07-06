# -*- coding: utf-8 -*-#

from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.viewsets import ModelViewSet

from core.api.permissions import BaseApiPermissionMixin
from core.utils import get_formatted_logger
from note.models import Note
from note.serializers import NoteSerializer

logger = get_formatted_logger()


class NoteViewSet(ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    perm_slug = "note.note"
    queryset = Note.objects.all()
    authentication_classes = [TokenAuthentication]
