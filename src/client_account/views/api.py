# -*- coding: utf-8 -*-#
from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.viewsets import ModelViewSet

from client_account.models import ClientAccount
from client_account.serializers import ClientAccountSerializer
from core.api.permissions import BaseApiPermissionMixin
from core.utils import get_formatted_logger

logger = get_formatted_logger()


class ClientAccountViewSet(ModelViewSet):
    serializer_class = ClientAccountSerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    # parser_classes = [parsers.FormParser, parsers.MultiPartParser]
    perm_slug = "client_account.clientaccount"
    queryset = ClientAccount.objects.all()
    http_method_names = ["post"]
    authentication_classes = [TokenAuthentication]
