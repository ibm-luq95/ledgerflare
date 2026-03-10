import traceback
from datetime import timedelta

from django.db.models import Count
from django.db.models import F
from django.db.models import Q
from django.utils import timezone
from rest_framework import permissions
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from core.api.permissions import ManagerApiPermission
from core.choices import BeachWoodUserTypeEnum
from core.constants.status_labels import CON_ARCHIVED
from core.constants.status_labels import CON_COMPLETED
from core.constants.status_labels import CON_IN_PROGRESS
from core.constants.status_labels import CON_NOT_STARTED
from core.constants.status_labels import CON_PAST_DUE
from core.utils import get_formatted_logger
from core.utils.developments.debugging_print_object import DebuggingPrint
from job.models import JobProxy
from special_assignment.models import SpecialAssignmentProxy
from task.models import TaskProxy


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
            completed_jobs_count = JobProxy.objects.filter(
                status=CON_COMPLETED
            ).count()
            past_due_jobs_count = JobProxy.objects.filter(
                status=CON_PAST_DUE
            ).count()
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


class ManagerKPIStatsAPIView(APIView):
    """
    Returns all KPI statistics for the manager dashboard.

    GET /api/v1/manager/kpi-stats/

    Caching: 60 seconds
    """

    permission_classes = (permissions.IsAuthenticated, ManagerApiPermission)
    http_method_names = ["get"]
    authentication_classes = [TokenAuthentication]

    def get(self, request: Request, *args, **kwargs):
        try:
            today = timezone.now().date()

            # Basic counts
            staff_count = BWUser.objects.filter(
                user_type=BeachWoodUserTypeEnum.BOOKKEEPER, is_active=True
            ).count()

            clients_count = ClientProxy.objects.filter(is_active=True).count()
            jobs_count = JobProxy.objects.count()
            assignments_count = SpecialAssignmentProxy.objects.count()
            task_count = TaskProxy.objects.count()

            # Past due jobs: status=PAST_DUE OR (due_date < today AND not completed)
            past_due_jobs_count = (
                JobProxy.objects.filter(
                    Q(status=CON_PAST_DUE)
                    | (Q(due_date__lt=today) & ~Q(status=CON_COMPLETED))
                )
                .distinct()
                .count()
            )

            # Completed jobs
            completed_jobs_count = JobProxy.objects.filter(
                status=CON_COMPLETED
            ).count()

            # Job completion rate
            job_completion_rate = 0.0
            if jobs_count > 0:
                job_completion_rate = round(
                    (completed_jobs_count / jobs_count) * 100, 1
                )

            # Tasks not completed (IN_PROGRESS or NOT_STARTED)
            tasks_not_completed_count = TaskProxy.objects.filter(
                status__in=[CON_NOT_STARTED, CON_IN_PROGRESS]
            ).count()

            # Jobs needing info
            jobs_need_info_count = JobProxy.objects.filter(state="NEED_INFO").count()

            data = {
                "staff_count": staff_count,
                "clients_count": clients_count,
                "jobs_count": jobs_count,
                "assignments_count": assignments_count,
                "past_due_jobs_count": past_due_jobs_count,
                "task_count": task_count,
                "completed_jobs_count": completed_jobs_count,
                "job_completion_rate": job_completion_rate,
                "tasks_not_completed_count": tasks_not_completed_count,
                "jobs_need_info_count": jobs_need_info_count,
            }

            return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ManagerPastDueJobsAPIView(APIView):
    """
    Returns past due jobs for the manager dashboard table.

    GET /api/v1/manager/past-due-jobs/?limit=10

    Caching: 120 seconds

    Filters by:
    - status=CON_PAST_DUE, OR
    - due_date < today AND status != CON_COMPLETED
    """

    permission_classes = (permissions.IsAuthenticated, ManagerApiPermission)
    http_method_names = ["get"]
    authentication_classes = [TokenAuthentication]

    def get(self, request: Request, *args, **kwargs):
        try:
            limit = int(request.GET.get("limit", 10))
            today = timezone.now().date()

            # Past due jobs: status=PAST_DUE OR (due_date < today AND not completed)
            jobs = (
                JobProxy.objects.select_related("client", "managed_by")
                .filter(
                    Q(status=CON_PAST_DUE)
                    | (Q(due_date__lt=today) & ~Q(status=CON_COMPLETED))
                )
                .distinct()
                .order_by("-created_at")[:limit]
            )

            data = []
            for job in jobs:
                data.append({
                    "id": job.id,
                    "title": job.title,
                    "client_name": job.client.name if job.client else "Unassigned",
                    "client_id": job.client.id if job.client else None,
                    "assigned_to": (
                        job.managed_by.fullname if job.managed_by else "Unassigned"
                    ),
                    "due_date": (
                        job.due_date.strftime("%Y-%m-%d") if job.due_date else None
                    ),
                    "status": job.status,
                    "status_display": (
                        job.get_status_display()
                        if hasattr(job, "get_status_display")
                        else job.status
                    ),
                    "url": f"/dashboard/jobs/{job.id}/",
                })
            # DebuggingPrint.pprint(data)
            return Response(
                data={"count": len(data), "data": data}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ManagerTasksThisWeekAPIView(APIView):
    """
    Returns active tasks (not completed) for the manager dashboard table.

    GET /api/v1/manager/tasks-this-week/?limit=15

    Caching: 120 seconds
    """

    permission_classes = (permissions.IsAuthenticated, ManagerApiPermission)
    http_method_names = ["get"]
    authentication_classes = [TokenAuthentication]

    def get(self, request: Request, *args, **kwargs):
        try:
            limit = int(request.GET.get("limit", 10))

            # Active tasks (not completed) - ordered by created_at
            tasks = (
                TaskProxy.objects.select_related("job", "job__client")
                .filter(
                    status__in=[CON_NOT_STARTED, CON_IN_PROGRESS],
                )
                .order_by("-created_at")[:limit]
            )

            data = []
            for task in tasks:
                data.append({
                    "id": task.id,
                    "title": task.title,
                    "job_title": task.job.title if task.job else "Unknown Job",
                    "job_id": task.job.id if task.job else None,
                    "client_name": (
                        task.job.client.name
                        if task.job and task.job.client
                        else "Unknown Client"
                    ),
                    "client_id": (
                        task.job.client.id if task.job and task.job.client else None
                    ),
                    "status": task.status,
                    "status_display": (
                        task.get_status_display()
                        if hasattr(task, "get_status_display")
                        else task.status
                    ),
                    "url": f"/dashboard/tasks/{task.id}/",
                })

            return Response(
                data={"count": len(data), "data": data}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ManagerStaffWorkloadAPIView(APIView):
    """
    Returns staff workload distribution for the manager dashboard chart.

    GET /api/v1/manager/staff-workload/

    Caching: 300 seconds
    """

    permission_classes = (permissions.IsAuthenticated, ManagerApiPermission)
    http_method_names = ["get"]
    authentication_classes = [TokenAuthentication]

    def get(self, request: Request, *args, **kwargs):
        try:
            # Get all active bookkeepers with their job/task counts
            staff = (
                BWUser.objects.filter(
                    user_type=BeachWoodUserTypeEnum.BOOKKEEPER, is_active=True
                )
                .annotate(
                    active_jobs=Count(
                        "jobs",
                        filter=Q(
                            jobs__status__in=[CON_NOT_STARTED, CON_IN_PROGRESS]
                        ),
                    ),
                    completed_jobs=Count(
                        "jobs", filter=Q(jobs__status=CON_COMPLETED)
                    ),
                    pending_tasks=Count(
                        "jobs__tasks",
                        filter=Q(
                            jobs__tasks__status__in=[
                                CON_NOT_STARTED,
                                CON_IN_PROGRESS,
                            ]
                        ),
                    ),
                )
                .order_by("-active_jobs")
            )

            labels = []
            active_jobs_data = []
            completed_jobs_data = []
            pending_tasks_data = []

            for member in staff:
                name = member.fullname or f"{member.first_name} {member.last_name}"
                labels.append(name)
                active_jobs_data.append(member.active_jobs or 0)
                completed_jobs_data.append(member.completed_jobs or 0)
                pending_tasks_data.append(member.pending_tasks or 0)

            data = {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Active Jobs",
                        "data": active_jobs_data,
                        "backgroundColor": "#3B82F6",
                        "borderColor": "#2563EB",
                        "borderWidth": 1,
                    },
                    {
                        "label": "Completed Jobs",
                        "data": completed_jobs_data,
                        "backgroundColor": "#22C55E",
                        "borderColor": "#16A34A",
                        "borderWidth": 1,
                    },
                    {
                        "label": "Pending Tasks",
                        "data": pending_tasks_data,
                        "backgroundColor": "#EAB308",
                        "borderColor": "#CA8A04",
                        "borderWidth": 1,
                    },
                ],
            }

            return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ManagerJobCompletionRateAPIView(APIView):
    """
    Returns job completion rate with trend for the manager dashboard.

    GET /api/v1/manager/job-completion-rate/

    Caching: 300 seconds
    """

    permission_classes = (permissions.IsAuthenticated, ManagerApiPermission)
    http_method_names = ["get"]
    authentication_classes = [TokenAuthentication]

    def get(self, request: Request, *args, **kwargs):
        try:
            now = timezone.now()

            # Current period (all time)
            total_jobs = JobProxy.objects.count()
            completed_jobs = JobProxy.objects.filter(status=CON_COMPLETED).count()

            # Calculate completion rate
            completion_rate = 0.0
            if total_jobs > 0:
                completion_rate = round((completed_jobs / total_jobs) * 100, 1)

            # Calculate trend (compare last 30 days vs previous 30 days)
            last_30_days = now - timedelta(days=30)
            previous_30_days = now - timedelta(days=60)

            # Last 30 days completion rate
            last_30_total = JobProxy.objects.filter(
                created_at__gte=last_30_days
            ).count()
            last_30_completed = JobProxy.objects.filter(
                created_at__gte=last_30_days, status=CON_COMPLETED
            ).count()
            last_30_rate = 0.0
            if last_30_total > 0:
                last_30_rate = (last_30_completed / last_30_total) * 100

            # Previous 30 days completion rate
            previous_30_total = JobProxy.objects.filter(
                created_at__gte=previous_30_days, created_at__lt=last_30_days
            ).count()
            previous_30_completed = JobProxy.objects.filter(
                created_at__gte=previous_30_days,
                created_at__lt=last_30_days,
                status=CON_COMPLETED,
            ).count()
            previous_30_rate = 0.0
            if previous_30_total > 0:
                previous_30_rate = (previous_30_completed / previous_30_total) * 100

            # Calculate trend
            trend = round(last_30_rate - previous_30_rate, 1)
            trend_positive = trend >= 0

            data = {
                "completion_rate": completion_rate,
                "completed_jobs": completed_jobs,
                "total_jobs": total_jobs,
                "trend": abs(trend),
                "trend_positive": trend_positive,
            }

            return Response(status=status.HTTP_200_OK, data=data)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
