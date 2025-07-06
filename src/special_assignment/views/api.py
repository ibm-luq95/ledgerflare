# -*- coding: utf-8 -*-#

from rest_framework import permissions, parsers, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.api.permissions import BaseApiPermissionMixin
from core.utils import get_formatted_logger, debugging_print
from core.utils.developments.debugging_print_object import DebuggingPrint
from special_assignment.models import SpecialAssignmentProxy
from special_assignment.serializers import SpecialAssignmentSerializer

logger = get_formatted_logger()


class SpecialAssignmentViewSet(ModelViewSet):
    serializer_class = SpecialAssignmentSerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    parser_classes = [parsers.FormParser, parsers.MultiPartParser]
    perm_slug = "special_assignment.specialassignment"
    authentication_classes = [TokenAuthentication]
    queryset = SpecialAssignmentProxy.objects.all()

    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     # serializer.is_valid(raise_exception=True)
    #     serializer.is_valid(raise_exception=False)
    #     DebuggingPrint.print(serializer.data)
    #     self.perform_create(serializer)
    #     headers = self.get_success_headers(serializer.data)
    #     return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
