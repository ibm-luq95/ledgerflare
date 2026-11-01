# -*- coding: utf-8 -*-#
import traceback

from django.contrib.auth.models import Permission
from django.db.transaction import atomic
from rest_framework import permissions
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from beach_wood_user.models import BWUser
from bookkeeper.models import BookkeeperProxy
from client.models import ClientProxy
from core.choices import BeachWoodUserTypeEnum
from core.api.throttling import AuthEndpointRateThrottle
from core.api.permissions import ManagerApiPermission
from core.utils import get_formatted_logger
from core.utils.developments.debugging_print_object import DebuggingPrint

logger = get_formatted_logger()


ALLOWED_OPERATIONAL_PERMISSION_APPS = frozenset({
    "client",
    "job",
    "task",
    "note",
    "document",
    "special_assignment",
    "client_category",
    "important_contact",
})


class UpdateStaffPermissionsApiView(APIView):
    permission_classes = (permissions.IsAuthenticated, ManagerApiPermission)
    throttle_classes = [AuthEndpointRateThrottle]
    http_method_names = ["post"]

    def post(self, request: Request, *args, **kwargs):
        # Enforce strict role check: only Managers and Superusers can edit permissions
        if not (
            request.user.is_superuser
            or request.user.user_type == BeachWoodUserTypeEnum.MANAGER
        ):
            return Response(
                {
                    "detail": "Only managers and administrators can update staff permissions."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            with atomic():
                data = dict()
                post_data = request.data
                user = BWUser.objects.get(pk=post_data["user"])
                data["user"] = user.pk

                post_permissions = post_data.get("permissions", [])
                permissions_objs = list(
                    Permission.objects.filter(pk__in=post_permissions).select_related(
                        "content_type"
                    )
                )

                # Validate permissions against allowable operational apps whitelist
                disallowed = [
                    perm
                    for perm in permissions_objs
                    if perm.content_type.app_label
                    not in ALLOWED_OPERATIONAL_PERMISSION_APPS
                ]
                if disallowed:
                    return Response(
                        {
                            "detail": (
                                "Cannot assign administrative or system permissions."
                            )
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

                # delete all current permissions
                user.user_permissions.clear()
                user.save()
                user.user_permissions.add(*permissions_objs)
                user.save()
                return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            logger.error(traceback.format_exc())
            DebuggingPrint.print_exception()
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data={"detail": "An internal error occurred."},
            )


class AssignClientToBookkeeperApiView(APIView):
    permission_classes = (permissions.IsAuthenticated, ManagerApiPermission)
    throttle_classes = [AuthEndpointRateThrottle]
    http_method_names = ["post"]

    def post(self, request: Request, *args, **kwargs):
        try:
            with atomic():
                data = dict()
                post_data = request.data
                bookkeeper = BookkeeperProxy.objects.get(pk=post_data["bookkeeper"])
                clients = ClientProxy.objects.filter(pk__in=post_data["client"])
                clients_list = [cl for cl in clients]
                bookkeeper.clients.clear()
                bookkeeper.clients.add(*clients_list)
                bookkeeper.save()

                return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            logger.error(traceback.format_exc())
            DebuggingPrint.print_exception()
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                data={"detail": "An internal error occurred."},
            )
