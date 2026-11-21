# -*- coding: utf-8 -*-#
from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.viewsets import ModelViewSet

from client_account.models import ClientAccountProxy
from client_account.serializers import ClientAccountSerializer
from core.api.mixins import RoleScopedQuerysetMixin
from core.api.permissions import BaseApiPermissionMixin
from core.utils import get_formatted_logger

logger = get_formatted_logger()


class ClientAccountViewSet(RoleScopedQuerysetMixin, ModelViewSet):
    serializer_class = ClientAccountSerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    # parser_classes = [parsers.FormParser, parsers.MultiPartParser]
    perm_slug = "client_account.clientaccount"
    queryset = ClientAccountProxy.objects.all()
    filterset_fields = ["account_name", "client", "status", "is_deleted"]
    search_fields = ["account_name", "account_email"]
    ordering_fields = ["created_at", "updated_at", "account_name"]
    ordering = ["account_name"]
    http_method_names = ["post"]

    def scope_queryset_for_bookkeeper(self, queryset, bookkeeper):
        return queryset.filter(client__bookkeepers=bookkeeper)

    def scope_queryset_for_cfo(self, queryset, cfo):
        return queryset.filter(client__cfos=cfo)
