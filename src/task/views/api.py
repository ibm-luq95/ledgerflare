# -*- coding: utf-8 -*-#

from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.viewsets import ModelViewSet

from core.api.permissions import BaseApiPermissionMixin
from core.utils import get_formatted_logger
from task.models import TaskProxy
from task.serializers import TaskSerializer

logger = get_formatted_logger()


class TaskViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    perm_slug = "task.task"
    authentication_classes = [TokenAuthentication]
    queryset = TaskProxy.objects.all()
