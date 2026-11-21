"""Views for Task management in LedgerFlare."""

from __future__ import annotations

from typing import Any

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q, QuerySet
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from core.cache import BWSiteSettingsViewMixin
from core.choices import TaskStatusEnum, TaskTypeEnum
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.constants.users import (
    CON_ASSISTANT,
    CON_BOOKKEEPER,
    CON_CFO,
    CON_MANAGER,
)
from core.views.mixins import (
    BWBaseListViewMixin,
    BWLoginRequiredMixin,
    BWObjectAccessRequiredMixin,
)
from core.views.mixins.bookkeeper_pass_related_mixin import (
    BookkeeperPassRelatedMixin,
)
from task.filters import TaskFilter
from task.forms import TaskForm
from task.models import TaskProxy
from task.services import TaskExportService


def get_scoped_task_queryset(user: Any) -> QuerySet[TaskProxy]:
    """Return base queryset scoped to the current user's role."""
    if user.is_superuser or user.user_type == CON_MANAGER:
        return TaskProxy.objects.all()

    match user.user_type:
        case str() as t if t == CON_BOOKKEEPER:
            return TaskProxy.objects.filter(
                Q(job__managed_by=user) | Q(job__client__bookkeepers__user=user)
            ).distinct()
        case str() as t if t == CON_ASSISTANT:
            return TaskProxy.objects.filter(Q(job__managed_by=user)).distinct()
        case str() as t if t == CON_CFO:
            return TaskProxy.objects.filter(Q(job__client__cfos__user=user)).distinct()
        case _:
            return TaskProxy.objects.none()


class TaskListView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    ListView,
):
    """View to display list of tasks with role-based scoping and KPI stats."""

    permission_required = "task.can_view_list"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "task/list.html"
    model = TaskProxy
    paginate_by = LIST_VIEW_PAGINATE_BY
    list_type = "list"
    is_show_create_btn = True
    is_filters_enabled = True
    is_actions_menu_enabled = True
    is_header_enabled = True
    is_footer_enabled = True
    show_info_icon = True
    page_title = _("Tasks")
    page_header = _("Tasks".title())
    component_path = "bw_components/task/table_list.html"
    actions_base_url = "dashboard:task"
    filter_cancel_url = "dashboard:task:list"
    table_header_title = _("C")
    pagination_list_url_name = "dashboard:task:list"
    actions_items = "update,delete"
    base_url_name = "dashboard:task"
    empty_label = _("tasks")
    subtitle = _(
        "Monitor daily action items, subtasks, assignments, and workflow completion status."
    )

    def _get_base_queryset(self):
        """Return base queryset scoped to the current user's role."""
        return get_scoped_task_queryset(self.request.user)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Aggregate KPI stats and construct context for template."""
        context = super().get_context_data(**kwargs)
        context.setdefault("extra_context", {})
        context.setdefault(
            "filter_form_id",
            getattr(self, "filter_form_id", "tasksFilterForm"),
        )
        context["filter_form"] = getattr(
            self,
            "filterset",
            TaskFilter(self.request.GET, queryset=self._get_base_queryset()),
        ).form
        context["export_csv_url"] = reverse_lazy("dashboard:task:export_csv")
        context["export_excel_url"] = reverse_lazy("dashboard:task:export_excel")
        context["export_url"] = reverse_lazy("dashboard:task:export")
        context.setdefault(
            "info_details",
            {
                "tooltip_txt": BW_INFO_MODAL_CSS_CLASSES.get("task").get("tooltip_txt"),
                "modal_css_id": BW_INFO_MODAL_CSS_CLASSES.get("task").get("cssID"),
            },
        )
        context.setdefault("table_header_subtitle", _("Tasks for all jobs"))

        if self.request.GET:
            context["title"] = _("Filtered Tasks")
        else:
            context["title"] = _("Tasks")

        today = timezone.now().date()
        base_qs = self._get_base_queryset()
        kpi_stats = base_qs.aggregate(
            total_tasks=Count("id", distinct=True),
            in_progress_tasks=Count(
                "id", filter=Q(status=TaskStatusEnum.IN_PROGRESS), distinct=True
            ),
            past_due_tasks=Count(
                "id",
                filter=(
                    Q(status=TaskStatusEnum.PAST_DUE)
                    | (
                        Q(job__due_date__lt=today)
                        & ~Q(status=TaskStatusEnum.COMPLETED)
                        & ~Q(status=TaskStatusEnum.ARCHIVED)
                    )
                ),
                distinct=True,
            ),
            urgent_tasks=Count(
                "id", filter=Q(task_type=TaskTypeEnum.URGENT), distinct=True
            ),
            completed_tasks=Count(
                "id", filter=Q(status=TaskStatusEnum.COMPLETED), distinct=True
            ),
        )
        context["kpi_stats"] = kpi_stats
        context.setdefault("total_records", kpi_stats.get("total_tasks", 0))

        return context

    def get_queryset(self):
        """Return eager-loaded, column-projected, and filtered queryset."""
        queryset = self._get_base_queryset()
        queryset = queryset.select_related(
            "job", "job__client", "job__managed_by"
        ).only(
            "id",
            "title",
            "hints",
            "status",
            "task_type",
            "is_completed",
            "created_at",
            "updated_at",
            "job__id",
            "job__title",
            "job__due_date",
            "job__client__id",
            "job__client__name",
            "job__managed_by__id",
            "job__managed_by__first_name",
            "job__managed_by__last_name",
            "job__managed_by__email",
            "job__managed_by__user_type",
        )
        self.filterset = TaskFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs


class TaskCreateView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    BookkeeperPassRelatedMixin,
    CreateView,
):
    """View to handle creation of a new task."""

    permission_required = "task.add_task"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "task/create.html"
    form_class = TaskForm
    success_message = _("Task created successfully")
    success_url = reverse_lazy("dashboard:task:list")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Construct context data for task create view."""
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Create task"))
        return context


class TaskUpdateView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    BookkeeperPassRelatedMixin,
    UpdateView,
):
    """View to handle updating an existing task."""

    permission_required = "task.change_task"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "task/update.html"
    form_class = TaskForm
    success_message = _("Task updated successfully")
    model = TaskProxy

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Construct context data for task update view."""
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Update task"))
        prev_url = self.request.META.get("HTTP_REFERER")
        self.request.session["prev_url"] = prev_url
        self.request.session.modified = True

        return context

    def get_success_url(self) -> str:
        """Return the URL to redirect to after processing a valid form."""
        prev_url = self.request.session.get("prev_url")
        self.request.session.delete("prev_url")
        self.request.session.modified = True
        if prev_url is not None:
            return str(prev_url)
        return str(reverse_lazy("dashboard:task:list"))


class TaskDeleteView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    SuccessMessageMixin,
    DeleteView,
):
    """View to handle deletion of an existing task."""

    template_name = "core/crudl/delete.html"
    permission_required = "task.delete_task"
    permission_denied_message = _("You do not have permission to access this page.")
    model = TaskProxy
    success_message = _("Task deleted successfully")
    success_url = reverse_lazy("dashboard:task:list")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Construct context data for task delete view."""
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Delete task"))
        context.setdefault("cancel_url", "dashboard:task:list")
        context.setdefault("object", self.get_object())
        context.setdefault("object_name", "task")
        context.setdefault("form_css_id", "taskDeleteForm")
        return context


class TaskQuickPeekView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    DetailView,
):
    """Render lightweight partial HTML for Task Quick Peek Slide-Over Drawer."""

    permission_required = "task.can_view_list"
    permission_denied_message = _("You do not have permission to view task details.")
    model = TaskProxy
    template_name = "bw_components/task/quick_peek_content.html"

    def get_queryset(self):
        """Return eager-loaded task for quick peek display."""
        return (
            super()
            .get_queryset()
            .select_related("job", "job__client", "job__managed_by")
            .prefetch_related("notes", "documents")
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Populate quick peek context with task, notes, and documents."""
        context = super().get_context_data(**kwargs)
        task = self.get_object()
        context["task"] = task
        context["notes"] = task.notes.all()[:5]
        context["documents"] = task.documents.all()[:5]
        return context


class BaseTaskExportView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    View,
):
    """Base class for exporting filtered tasks."""

    permission_required = "task.can_view_list"
    permission_denied_message = _("You do not have permission to export tasks.")

    def get_queryset(self) -> QuerySet[TaskProxy]:
        """Return eager-loaded filtered tasks matching the request query params."""
        base_qs = get_scoped_task_queryset(self.request.user)
        base_qs = base_qs.select_related(
            "job",
            "job__client",
            "job__managed_by",
        )
        filterset = TaskFilter(self.request.GET, queryset=base_qs)
        return filterset.qs


class TaskExportCsvView(BaseTaskExportView):
    """View to export tasks to CSV format."""

    def get(self, request: Any, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handle GET request to generate and download CSV file."""
        tasks = self.get_queryset()
        service = TaskExportService()
        return service.export_csv(tasks)


class TaskExportExcelView(BaseTaskExportView):
    """View to export tasks to XLSX format."""

    def get(self, request: Any, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handle GET request to generate and download Excel workbook."""
        tasks = self.get_queryset()
        service = TaskExportService()
        return service.export_xlsx(tasks)


class TaskExportView(BaseTaskExportView):
    """Unified view to export tasks based on format query param ('csv' or 'xlsx')."""

    def get(self, request: Any, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handle GET request to generate either CSV or Excel file."""
        tasks = self.get_queryset()
        export_format = request.GET.get("format", "csv").lower()
        service = TaskExportService()
        if export_format in ["xlsx", "excel"]:
            return service.export_xlsx(tasks)
        return service.export_csv(tasks)
