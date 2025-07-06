# -*- coding: utf-8 -*-#

from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.viewsets import ModelViewSet

from core.api.permissions import BaseApiPermissionMixin
from core.utils import get_formatted_logger
from staff_briefcase.models import StaffNotes
from staff_briefcase.serializers import StaffNotesSerializer

logger = get_formatted_logger()


class StaffNotesViewSet(ModelViewSet):
    serializer_class = StaffNotesSerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    perm_slug = "staff_briefcase.staffnotes"
    queryset = StaffNotes.objects.all()
    authentication_classes = [TokenAuthentication]
