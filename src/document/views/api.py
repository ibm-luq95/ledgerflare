# -*- coding: utf-8 -*-#

from rest_framework import permissions, parsers
from rest_framework.authentication import TokenAuthentication
from rest_framework.viewsets import ModelViewSet

from core.api.permissions import BaseApiPermissionMixin
from core.utils import get_formatted_logger
from document.models import Document
from document.serializers import DocumentSerializer

logger = get_formatted_logger()


class DocumentViewSet(ModelViewSet):
    serializer_class = DocumentSerializer
    parser_classes = [
        parsers.FormParser,
        parsers.MultiPartParser,
    ]
    authentication_classes = [TokenAuthentication]
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    perm_slug = "document.document"
    queryset = Document.objects.all()
