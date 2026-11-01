# -*- coding: utf-8 -*-#

from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.viewsets import ModelViewSet

from core.api.mixins import RoleScopedQuerysetMixin, CachedViewSetResponseMixin
from core.api.permissions import BaseApiPermissionMixin
from core.utils import get_formatted_logger
from job_category.models import JobCategory
from job_category.serializers import JobCategorySerializer

logger = get_formatted_logger()


class JobCategoryViewSet(CachedViewSetResponseMixin, RoleScopedQuerysetMixin, ModelViewSet):
    serializer_class = JobCategorySerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    perm_slug = "job_category.jobcategory"
    queryset = JobCategory.objects.all()
    filterset_fields = ["name", "is_deleted"]
    search_fields = ["name"]
    ordering_fields = ["created_at", "updated_at", "name"]
    ordering = ["name"]

    def scope_queryset_for_bookkeeper(self, queryset, bookkeeper):
        return queryset.filter(jobs__bookkeeper=bookkeeper).distinct()

    def scope_queryset_for_cfo(self, queryset, cfo):
        return queryset.filter(jobs__client__cfos=cfo).distinct()
