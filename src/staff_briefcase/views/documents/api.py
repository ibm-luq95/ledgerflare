# -*- coding: utf-8 -*-#

from rest_framework import permissions, parsers
from rest_framework.authentication import TokenAuthentication
from rest_framework.viewsets import ModelViewSet

from core.api.permissions import BaseApiPermissionMixin
from core.utils import get_formatted_logger
from staff_briefcase.models import StaffDocuments
from staff_briefcase.serializers import StaffDocumentsSerializer

logger = get_formatted_logger()


class StaffDocumentsViewSet(ModelViewSet):
    parser_classes = [
        parsers.FormParser,
        parsers.MultiPartParser,
    ]
    authentication_classes = [TokenAuthentication]
    serializer_class = StaffDocumentsSerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    perm_slug = "staff_briefcase.staffdocuments"
    queryset = StaffDocuments.objects.all()
