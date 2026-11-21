import traceback

from django.db import models
from django.utils.translation import gettext as _
from rest_framework import permissions
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import APIException
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from core.api.permissions import BaseApiPermissionMixin
from core.api.mixins import RoleScopedQuerysetMixin
from core.utils import get_formatted_logger
from job.models import JobProxy
from job.serializers.job import JobSerializer


logger = get_formatted_logger()


class JobViewSet(RoleScopedQuerysetMixin, ModelViewSet):
    serializer_class = JobSerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    perm_slug = "job.job"
    queryset = JobProxy.objects.all()
    filterset_fields = [
        "status",
        "state",
        "job_type",
        "client",
        "managed_by",
        "is_deleted",
    ]
    search_fields = ["title", "description", "client__name"]
    ordering_fields = ["created_at", "updated_at", "title", "status", "due_date"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related("client", "managed_by").prefetch_related(
            "tasks", "categories"
        )

    def scope_queryset_for_bookkeeper(self, queryset, bookkeeper):
        return queryset.filter(
            models.Q(managed_by=bookkeeper.user)
            | models.Q(client__bookkeepers=bookkeeper)
        ).distinct()

    def scope_queryset_for_cfo(self, queryset, cfo):
        return queryset.filter(client__cfos=cfo)


class UpdateJobApiView(RoleScopedQuerysetMixin, APIView):
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    perm_slug = "job.job"
    queryset = JobProxy.objects.all()

    def scope_queryset_for_bookkeeper(self, queryset, bookkeeper):
        return queryset.filter(
            models.Q(managed_by=bookkeeper.user)
            | models.Q(client__bookkeepers=bookkeeper)
        ).distinct()

    def scope_queryset_for_cfo(self, queryset, cfo):
        return queryset.filter(client__cfos=cfo)

    def put(self, request: Request, *args, **kwargs):
        try:
            data = request.data
            job_object = self.get_queryset().get(pk=data.get("jobId"))
            del data["jobId"]
            # debugging_print(data)

            # serializer = JobSerializer(instance=job_object, data=data, partial=True)
            serializer = JobSerializer(
                instance=job_object,
                data=data,
                context={"request": request},
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            # if not serializer.is_valid(raise_exception=True):
            #     raise APIException(serializer.errors)
            # debugging_print(serializer.validated_data)
            # raise APIException("stop")
            # serializer.update(job_object, serializer.validated_data)
            serializer.save()
            # tasks = data.get("tasks")
            # bookkeepers = data.get("bookkeeper")

            return Response(
                data={"job": serializer.data, "msg": _("Job updated successfully!")},
                status=status.HTTP_200_OK,
            )
        except APIException:
            # logger.error("API Exception")
            logger.error(traceback.format_exc())
            # logger.error(ex.detail)
            response_data = {
                "status": status.HTTP_400_BAD_REQUEST,
                # "user_error_msg": ex.detail,
                "user_error_msg": serializer.errors,
                # "user_error_msg": str(ex),
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            # debugging_print(ex)
            logger.error(traceback.format_exc())
            response_data = {
                "status": status.HTTP_400_BAD_REQUEST,
                "error": str(ex),
                "user_error_msg": _("Error while update job!"),
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
