# -*- coding: utf-8 -*-#

from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.viewsets import ModelViewSet

from core.api.permissions import BaseApiPermissionMixin
from core.utils import get_formatted_logger
from job_category.models import JobCategory
from job_category.serializers import JobCategorySerializer

logger = get_formatted_logger()


class JobCategoryViewSet(ModelViewSet):
    serializer_class = JobCategorySerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    perm_slug = "job_category.jobcategory"
    queryset = JobCategory.objects.all()
    authentication_classes = [TokenAuthentication]
