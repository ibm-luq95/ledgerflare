# -*- coding: utf-8 -*-#
import traceback
from typing import Literal

from django.db.transaction import atomic
from rest_framework import permissions, parsers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from beach_wood_user.models import BWUser
from core.api.permissions import BaseApiPermissionMixin
from core.utils import get_formatted_logger
from core.utils.developments.debugging_print_object import DebuggingPrint
from discussion.models import DiscussionProxy, DiscussionNotification
from discussion.serializers import DiscussionSerializer
from special_assignment.models import SpecialAssignmentNotification

logger = get_formatted_logger()


class DiscussionNotificationsApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    # perm_slug = "discussion.discussionnotifications"
    http_method_names = ["post"]

    def post(self, request: Request, *args, **kwargs):
        try:
            with atomic():
                data = dict()
                post_data = request.data
                user: BWUser = BWUser.objects.get(pk=post_data.get("user"))
                notification_object_lbl: Literal[
                    "SpecialAssignmentNotification", "DiscussionNotification"
                ] = post_data.get("notificationType")
                if notification_object_lbl == "DiscussionNotification":
                    discussion_notifications: DiscussionNotification = (
                        DiscussionNotification.objects.get(pk=post_data.get("pk"))
                    )
                    # validate it the recipient user match the user how clicked on the notifications
                    # if discussion_notifications.recipient == user:
                    discussion_notifications.is_read = True
                    discussion_notifications.save()
                elif notification_object_lbl == "SpecialAssignmentNotification":
                    special_assignment_notification: SpecialAssignmentNotification = (
                        SpecialAssignmentNotification.objects.get(pk=post_data.get("pk"))
                    )
                    # validate it the recipient user match the user how clicked on the notifications
                    # if special_assignment_notification.recipient == user:
                    special_assignment_notification.is_read = True
                    special_assignment_notification.save()
                # DebuggingPrint.pprint(locals())
                # DebuggingPrint.pprint(discussion_notifications.recipient)

                return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            logger.error(traceback.format_exc())
            DebuggingPrint.print_exception()
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data=str(e))


class DiscussionViewSet(ModelViewSet):
    serializer_class = DiscussionSerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    parser_classes = [parsers.FormParser, parsers.MultiPartParser]
    perm_slug = "discussion.discussion"
    queryset = DiscussionProxy.objects.all()


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
