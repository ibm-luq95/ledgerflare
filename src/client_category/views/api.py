# -*- coding: utf-8 -*-#

from rest_framework import permissions, parsers
from rest_framework.authentication import TokenAuthentication
from rest_framework.viewsets import ModelViewSet

from client.serializers import ClientSerializer
from client_category.models import ClientCategory
from client_category.serializers import ClientCategorySerializer
from core.api.permissions import BaseApiPermissionMixin
from core.utils import get_formatted_logger

logger = get_formatted_logger()


class ClientCategoryViewSet(ModelViewSet):
    serializer_class = ClientCategorySerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    perm_slug = "client_category.clientcategory"
    queryset = ClientCategory.objects.all()
    authentication_classes = [TokenAuthentication]
