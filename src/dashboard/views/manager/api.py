# -*- coding: utf-8 -*-#
import traceback

from rest_framework import permissions
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from core.api.permissions import ManagerApiPermission
from core.constants.status_labels import CON_COMPLETED, CON_PAST_DUE, CON_IN_PROGRESS
from core.utils import get_formatted_logger
from job.models import JobProxy
from special_assignment.models import SpecialAssignmentProxy

logger = get_formatted_logger()


class ManagementDashboardApiView(APIView):
    permission_classes = (permissions.IsAuthenticated, ManagerApiPermission)
    http_method_names = ["post"]
    authentication_classes = [TokenAuthentication]

    def post(self, request: Request, *args, **kwargs):
        try:
            data = dict()
            jobs_count = JobProxy.objects.count()
            data["jobs_count"] = jobs_count
            clients_count = ClientProxy.objects.count()
            data["clients_count"] = clients_count
            assignments_counts = SpecialAssignmentProxy.objects.count()
            data["assignments_counts"] = assignments_counts
            staff_users_count = BWUser.objects.count()
            data["staff_users_count"] = staff_users_count
            completed_jobs_count = JobProxy.objects.filter(status=CON_COMPLETED).count()
            past_due_jobs_count = JobProxy.objects.filter(status=CON_PAST_DUE).count()
            in_progress_jobs_count = JobProxy.objects.filter(
                status=CON_IN_PROGRESS
            ).count()
            data["jobs_statistics"] = {
                "completed_jobs_count": completed_jobs_count,
                "past_due_jobs_count": past_due_jobs_count,
                "in_progress_jobs_count": in_progress_jobs_count,
            }
            return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
