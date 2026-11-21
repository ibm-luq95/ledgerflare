"""Staff Job Workstation view module."""

from __future__ import annotations

import calendar
import datetime
from collections import defaultdict
from typing import Any, ClassVar

from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from client.models import ClientProxy
from core.cache import BWSiteSettingsViewMixin
from core.choices import JobStatusEnum
from core.constants.users import (
    CON_ASSISTANT,
    CON_BOOKKEEPER,
    CON_CFO,
    CON_MANAGER,
)
from core.views.mixins import BWLoginRequiredMixin
from job.models import JobProxy

User = get_user_model()


class JobWorkstationView(
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    TemplateView,
):
    """Interactive workstation view for managing scheduled jobs and tasks."""

    http_method_names: ClassVar[list[str]] = ["get"]
    template_name: str = "job/workstation.html"

    def get_template_names(self) -> list[str]:
        """Return partial or full template based on HTMX request."""
        if (
            self.request.headers.get("HX-Request") == "true"
            and self.request.GET.get("partial") == "content"
        ):
            return ["job/workstation_partials/content_wrapper.html"]
        return [self.template_name]

    def _get_target_period(self) -> tuple[int, int]:
        now = timezone.now()
        year_param = self.request.GET.get("year")
        month_param = self.request.GET.get("month")

        if year_param:
            try:
                year = int(year_param)
                month = int(month_param) if month_param else now.month
                if 1 <= month <= 12:
                    return year, month
            except ValueError, TypeError:
                pass

        # If not specified in URL, check if current period has jobs
        has_current = JobProxy.objects.filter(
            Q(period_year=str(now.year), period_month=str(now.month))
            | Q(due_date__year=now.year, due_date__month=now.month)
        ).exists()
        if has_current:
            return now.year, now.month

        # Fallback to the latest year and month with jobs
        latest_job = (
            JobProxy.objects
            .filter(period_year__isnull=False, period_month__isnull=False)
            .order_by("-period_year", "-due_date")
            .first()
        )
        if latest_job and latest_job.period_year and latest_job.period_month:
            try:
                return int(latest_job.period_year), int(latest_job.period_month)
            except ValueError, TypeError:
                pass

        return now.year, now.month

    def _scope_queryset_by_role(self, qs: QuerySet[JobProxy]) -> QuerySet[JobProxy]:
        user = self.request.user

        if user.is_superuser:
            staff_filter = self.request.GET.get("staff")
            if staff_filter:
                return qs.filter(
                    Q(managed_by__id=staff_filter)
                    | Q(client__bookkeepers__user__id=staff_filter)
                ).distinct()
            return qs

        match user.user_type:
            case str() as t if t == CON_BOOKKEEPER:
                return qs.filter(
                    Q(managed_by=user) | Q(client__bookkeepers__user=user)
                ).distinct()
            case str() as t if t == CON_ASSISTANT:
                return qs.filter(Q(managed_by=user)).distinct()
            case str() as t if t == CON_CFO:
                return qs.filter(Q(client__cfos__user=user)).distinct()
            case str() as t if t == CON_MANAGER:
                staff_filter = self.request.GET.get("staff")
                if staff_filter:
                    return qs.filter(
                        Q(managed_by__id=staff_filter)
                        | Q(client__bookkeepers__user__id=staff_filter)
                    ).distinct()
                return qs
            case _:
                return qs.none()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Aggregate calendar, kanban, agenda, and metrics context."""
        context = super().get_context_data(**kwargs)
        year, month = self._get_target_period()
        today = timezone.now().date()

        prev_date = datetime.date(year, month, 1) - datetime.timedelta(days=1)
        next_date = (
            datetime.date(year, month, 28) + datetime.timedelta(days=5)
        ).replace(day=1)

        base_qs = (
            JobProxy.objects
            .select_related("client", "managed_by")
            .prefetch_related(
                "tasks",
                "client__bookkeepers",
                "client__bookkeepers__user",
                "client__categories",
            )
            .filter(
                Q(period_year=str(year), period_month=str(month))
                | Q(due_date__year=year, due_date__month=month)
                | Q(start_date__year=year, start_date__month=month)
            )
        )

        scoped_qs = self._scope_queryset_by_role(base_qs)

        client_filter = self.request.GET.get("client")
        if client_filter:
            scoped_qs = scoped_qs.filter(client__id=client_filter)

        status_filter = self.request.GET.get("status")
        if status_filter:
            scoped_qs = scoped_qs.filter(status=status_filter)

        search_query = self.request.GET.get("search", "").strip()
        if search_query:
            scoped_qs = scoped_qs.filter(
                Q(title__icontains=search_query)
                | Q(client__name__icontains=search_query)
            )

        jobs_list = list(scoped_qs.distinct())

        jobs_by_day: dict[int, list[JobProxy]] = defaultdict(list)
        for job in jobs_list:
            if (
                job.due_date
                and job.due_date.year == year
                and job.due_date.month == month
            ):
                jobs_by_day[job.due_date.day].append(job)
            elif (
                job.start_date
                and job.start_date.year == year
                and job.start_date.month == month
            ):
                jobs_by_day[job.start_date.day].append(job)
            else:
                jobs_by_day[1].append(job)

        cal = calendar.Calendar(firstweekday=calendar.SUNDAY)
        month_days = cal.monthdayscalendar(year, month)
        calendar_weeks: list[list[dict[str, Any]]] = []

        for week in month_days:
            week_days: list[dict[str, Any]] = []
            for day_num in week:
                if day_num != 0:
                    day_date = datetime.date(year, month, day_num)
                    week_days.append({
                        "day": day_num,
                        "date": day_date,
                        "is_current_month": True,
                        "is_today": day_date == today,
                        "jobs": jobs_by_day.get(day_num, []),
                    })
                else:
                    week_days.append({
                        "day": 0,
                        "date": None,
                        "is_current_month": False,
                        "is_today": False,
                        "jobs": [],
                    })
            calendar_weeks.append(week_days)

        kanban_columns: dict[str, list[JobProxy]] = {
            "not_started": [
                j
                for j in jobs_list
                if j.status in [JobStatusEnum.NOT_STARTED, JobStatusEnum.DRAFT]
            ],
            "in_progress": [
                j for j in jobs_list if j.status == JobStatusEnum.IN_PROGRESS
            ],
            "past_due": [j for j in jobs_list if j.status == JobStatusEnum.PAST_DUE],
            "completed": [
                j
                for j in jobs_list
                if j.status in [JobStatusEnum.COMPLETED, JobStatusEnum.ARCHIVED]
            ],
        }

        agenda_groups: dict[str, list[JobProxy]] = {
            "overdue": [
                j
                for j in jobs_list
                if j.due_date
                and j.due_date < today
                and j.status != JobStatusEnum.COMPLETED
            ],
            "today": [
                j
                for j in jobs_list
                if j.due_date
                and j.due_date == today
                and j.status != JobStatusEnum.COMPLETED
            ],
            "this_week": [
                j
                for j in jobs_list
                if j.due_date
                and today < j.due_date <= today + datetime.timedelta(days=7)
                and j.status != JobStatusEnum.COMPLETED
            ],
            "upcoming": [
                j
                for j in jobs_list
                if j.due_date
                and j.due_date > today + datetime.timedelta(days=7)
                and j.status != JobStatusEnum.COMPLETED
            ],
            "completed": [j for j in jobs_list if j.status == JobStatusEnum.COMPLETED],
        }

        total_pending_tasks = sum(
            len([t for t in j.tasks.all() if not t.is_completed]) for j in jobs_list
        )

        metrics = {
            "total_jobs": len(jobs_list),
            "pending_tasks": total_pending_tasks,
            "in_progress": len(kanban_columns["in_progress"]),
            "completed": len(kanban_columns["completed"]),
        }

        is_manager_or_admin = (
            self.request.user.is_superuser
            or self.request.user.user_type in [CON_MANAGER, CON_CFO]
        )

        available_clients = ClientProxy.objects.filter(is_active=True).order_by("name")
        if self.request.user.user_type == CON_BOOKKEEPER:
            available_clients = available_clients.filter(
                bookkeepers__user=self.request.user
            )

        selected_staff = None
        staff_members: QuerySet[Any] = User.objects.none()
        if is_manager_or_admin:
            staff_members = User.objects.filter(
                is_active=True,
                user_type__in=[CON_BOOKKEEPER, CON_ASSISTANT, CON_MANAGER],
            ).order_by("first_name", "last_name")
            staff_filter = self.request.GET.get("staff")
            if staff_filter:
                selected_staff = staff_members.filter(id=staff_filter).first()

        # Build list of available years for quick jump
        db_years = list(
            JobProxy.objects
            .filter(period_year__isnull=False)
            .values_list("period_year", flat=True)
            .distinct()
        )
        years_set = {int(y) for y in db_years if y and y.isdigit()}
        years_set.add(timezone.now().year)
        years_set.add(year)
        available_years = sorted(list(years_set), reverse=True)

        months_list = [(i, calendar.month_name[i]) for i in range(1, 13)]

        active_filters_count = sum(
            1
            for val in [
                client_filter,
                status_filter,
                search_query,
                self.request.GET.get("staff"),
            ]
            if val
        )

        context.update({
            "title": _("Staff Workstation"),
            "current_year": year,
            "current_month_num": month,
            "current_month_name": calendar.month_name[month],
            "prev_year": prev_date.year,
            "prev_month": prev_date.month,
            "next_year": next_date.year,
            "next_month": next_date.month,
            "jobs": jobs_list,
            "calendar_weeks": calendar_weeks,
            "kanban_columns": kanban_columns,
            "agenda_groups": agenda_groups,
            "metrics": metrics,
            "clients": available_clients,
            "status_choices": JobStatusEnum.choices,
            "active_view": self.request.GET.get("view", "calendar"),
            "is_manager_or_admin": is_manager_or_admin,
            "staff_members": staff_members,
            "selected_staff": selected_staff,
            "selected_client_id": client_filter or "",
            "selected_status": status_filter or "",
            "search_query": search_query,
            "available_years": available_years,
            "months_list": months_list,
            "active_filters_count": active_filters_count,
        })

        return context
