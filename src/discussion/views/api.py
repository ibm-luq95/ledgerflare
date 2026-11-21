# -*- coding: utf-8 -*-#
import traceback
from typing import Literal

from django.db import models
from django.db.transaction import atomic
from rest_framework import permissions, parsers, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from beach_wood_user.models import BWUser
from core.api.permissions import BaseApiPermissionMixin
from core.api.mixins import RoleScopedQuerysetMixin
from core.utils import get_formatted_logger
from core.utils.developments.debugging_print_object import DebuggingPrint
from core.utils.html_sanitizer import sanitize_html
from discussion.models import DiscussionProxy
from discussion.serializers import DiscussionSerializer
from lf_notifications.models import NotificationRecipientProxy

logger = get_formatted_logger()


class DiscussionNotificationsApiView(APIView):
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    perm_slug = "discussion.discussionnotifications"
    http_method_names = ["post"]
    # authentication_classes = [TokenAuthentication]

    def post(self, request: Request, *args, **kwargs):
        try:
            with atomic():
                data = dict()
                post_data = request.data
                pk = post_data.get("pk")

                # Try to find and mark as read in the new system
                notification_recipient = NotificationRecipientProxy.objects.filter(
                    pk=pk, recipient=request.user
                ).first()

                if notification_recipient:
                    notification_recipient.mark_as_read()

                return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            logger.error(traceback.format_exc())
            DebuggingPrint.print_exception()
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data=str(e))


class DiscussionViewSet(RoleScopedQuerysetMixin, ModelViewSet):
    serializer_class = DiscussionSerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    parser_classes = [parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser]
    perm_slug = "discussion.discussion"
    queryset = DiscussionProxy.objects.all()
    filterset_fields = ["is_seen", "job", "special_assignment", "is_deleted"]
    search_fields = ["body"]
    ordering_fields = ["created_at", "updated_at"]
    ordering = ["created_at"]
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related(
            "job",
            "special_assignment",
            "sender",
            "manager",
            "manager__profile",
            "bookkeeper",
            "bookkeeper__profile",
            "assistant",
            "assistant__profile",
        )

    def perform_create(self, serializer):
        user = self.request.user
        extra_kwargs = {"sender": user}

        if "body" in serializer.validated_data:
            extra_kwargs["body"] = sanitize_html(serializer.validated_data["body"])

        match user.user_type:
            case "manager" if hasattr(user, "manager"):
                extra_kwargs["manager"] = user.manager.get_proxy_model()
            case "bookkeeper" if hasattr(user, "bookkeeper"):
                extra_kwargs["bookkeeper"] = user.bookkeeper.get_proxy_model()
            case "assistant" if hasattr(user, "assistant"):
                extra_kwargs["assistant"] = user.assistant.get_proxy_model()

        serializer.save(**extra_kwargs)

    def scope_queryset_for_bookkeeper(self, queryset, bookkeeper):
        return queryset.filter(
            models.Q(job__managed_by=bookkeeper.user)
            | models.Q(job__bookkeeper=bookkeeper)
            | models.Q(job__client__bookkeepers=bookkeeper)
            | models.Q(special_assignment__assigned_to=bookkeeper.user)
            | models.Q(special_assignment__assigned_by=bookkeeper.user)
            | models.Q(special_assignment__bookkeeper=bookkeeper)
            | models.Q(special_assignment__client__bookkeepers=bookkeeper)
        )

    def scope_queryset_for_cfo(self, queryset, cfo):
        return queryset.filter(
            models.Q(job__client__cfos=cfo)
            | models.Q(special_assignment__client__cfos=cfo)
        )


# class CreateDiscussionApiView(APIView):
#     parser_classes = [parsers.FormParser, parsers.MultiPartParser]
#     # parser_classes = [parsers.MultiPartParser]
#     permission_classes = [permissions.IsAuthenticated, BaseApiPermissionMixin]
#     perm_slug = "special_assignment.discussion"
#
#     def post(self, request: Request, *args, **kwargs):
#         serializer = ""
#         try:
#             data = request.data
#             # debugging_print(data)
#             serializer = DiscussionSerializer(data=data)
#             # raise APIException("Stop")
#             # debugging_print(serializer.is_valid())
#             # debugging_print(serializer)
#             if serializer.is_valid(raise_exception=True) is False:
#                 raise APIException(serializer.errors)
#             # debugging_print(serializer.validated_data)
#             serializer.save()
#             return Response(
#                 {"msg": _("Reply created successfully!")}, status=status.HTTP_201_CREATED
#             )
#         except APIException as ex:
#             # logger.error("API Exception")
#             logger.error(traceback.format_exc())
#             response_data = {
#                 "status": status.HTTP_400_BAD_REQUEST,
#                 # "user_error_msg": ex.detail,
#                 "user_error_msg": serializer.errors,
#             }
#             return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as ex:
#             # debugging_print(ex)
#             logger.error(traceback.format_exc())
#             response_data = {
#                 "status": status.HTTP_400_BAD_REQUEST,
#                 "error": str(ex),
#                 # "user_error_msg": "Error while create discussion!",
#                 # "user_error_msg": serializer.errors,
#             }
#             return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
