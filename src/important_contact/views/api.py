# -*- coding: utf-8 -*-#
from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.viewsets import ModelViewSet

from core.api.permissions import BaseApiPermissionMixin
from core.utils import get_formatted_logger
from important_contact.models import ImportantContact
from important_contact.serializers import ImportantContactSerializer

logger = get_formatted_logger()


class ImportantContactViewSet(ModelViewSet):
    serializer_class = ImportantContactSerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    # parser_classes = [parsers.FormParser, parsers.MultiPartParser]
    perm_slug = "important_contact.importantcontact"
    authentication_classes = [TokenAuthentication]
    queryset = ImportantContact.objects.all()
