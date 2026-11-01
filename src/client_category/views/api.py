# -*- coding: utf-8 -*-#

from rest_framework import permissions, parsers
from rest_framework.authentication import TokenAuthentication
from rest_framework.viewsets import ModelViewSet

from client.serializers import ClientSerializer
from client_category.models import ClientCategory
from client_category.serializers import ClientCategorySerializer
from core.api.mixins import RoleScopedQuerysetMixin, CachedViewSetResponseMixin
from core.api.permissions import BaseApiPermissionMixin
from core.utils import get_formatted_logger

logger = get_formatted_logger()


class ClientCategoryViewSet(CachedViewSetResponseMixin, RoleScopedQuerysetMixin, ModelViewSet):
    serializer_class = ClientCategorySerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    perm_slug = "client_category.clientcategory"
    queryset = ClientCategory.objects.all()
    filterset_fields = ["name", "is_deleted"]
    search_fields = ["name"]
    ordering_fields = ["created_at", "updated_at", "name"]
    ordering = ["name"]

    def scope_queryset_for_bookkeeper(self, queryset, bookkeeper):
        return queryset.filter(clients__bookkeepers=bookkeeper).distinct()

    def scope_queryset_for_cfo(self, queryset, cfo):
        return queryset.filter(clients__cfos=cfo).distinct()
