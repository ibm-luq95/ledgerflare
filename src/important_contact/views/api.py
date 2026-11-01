from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.viewsets import ModelViewSet

from core.api.mixins import RoleScopedQuerysetMixin
from core.api.permissions import BaseApiPermissionMixin
from core.utils import get_formatted_logger
from important_contact.models import ImportantContact
from important_contact.serializers import ImportantContactSerializer


logger = get_formatted_logger()


class ImportantContactViewSet(RoleScopedQuerysetMixin, ModelViewSet):
    serializer_class = ImportantContactSerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    # parser_classes = [parsers.FormParser, parsers.MultiPartParser]
    perm_slug = "important_contact.importantcontact"
    queryset = ImportantContact.objects.all()
    filterset_fields = ["contact_type", "client", "company", "is_deleted"]
    search_fields = ["contact_label", "contact_name", "email"]
    ordering_fields = ["created_at", "updated_at", "contact_name"]
    ordering = ["contact_name"]

    def scope_queryset_for_bookkeeper(self, queryset, bookkeeper):
        return queryset.filter(client__bookkeepers=bookkeeper).distinct()

    def scope_queryset_for_cfo(self, queryset, cfo):
        return queryset.filter(client__cfos=cfo).distinct()
