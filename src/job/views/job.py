import csv
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.http import Http404, HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView

from core.cache import BWSiteSettingsViewMixin
from core.choices import JobStateEnum
from core.choices import JobStatusEnum
from core.config.forms import BWFormRenderer
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.constants.status_labels import CON_ARCHIVED
from core.constants.status_labels import CON_COMPLETED
from core.constants.status_labels import CON_DRAFT
from core.constants.status_labels import CON_PAST_DUE
from core.constants.users import CON_ASSISTANT
from core.constants.users import CON_BOOKKEEPER
from core.constants.users import CON_CFO
from core.constants.users import CON_MANAGER
from core.models.querysets.base_queryset import BaseQuerySetMixin
from core.utils.developments.debugging_print_object import DebuggingPrint
from core.views.mixins import (
    BWBaseListViewMixin,
    BWLoginRequiredMixin,
    BWObjectAccessRequiredMixin,
)
from core.views.mixins.update_previous_mixin import UpdateReturnPreviousMixin
from discussion.forms import DiscussionMiniForm
from document.forms import DocumentForm
from job.filters import JobFilter
from job.filters.job_visibility_form import JobVisibilityForm
from job.forms import JobForm
from job.models import Job
from job.models import JobProxy
from job_category.forms import JobCategoryForm
from job_category.models import JobCategory
from manager.models import ManagerProxy
from note.forms import NoteForm
from special_assignment.forms import MiniSpecialAssignmentForm
from task.forms import TaskForm


class JobListView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    ListView,
):
    permission_required = "job.can_view_list"

    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "job/list.html"
    model = JobProxy

    paginate_by = LIST_VIEW_PAGINATE_BY
    list_type = "list"
    is_show_create_btn = True
    is_filters_enabled = True
    is_actions_menu_enabled = True
    is_header_enabled = True
    is_footer_enabled = True
    show_info_icon = False
    page_title = _("Jobs")
    page_header = _("Jobs".title())
    component_path = "bw_components/job/table_list.html"
    actions_base_url = "dashboard:job"
    filter_cancel_url = "dashboard:job:list"
    subtitle = _(
        "Track client engagements, recurring accounting workflows, deadlines, and project deliverables."
    )
    pagination_list_url_name = "dashboard:job:list"
    base_url_name = "dashboard:job"
    empty_label = _("jobs")
    actions_items = "details,update,delete"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.GET:
            context["title"] = _("Filtered jobs")
        else:
            context["title"] = _("Jobs")

        base_qs = JobProxy.objects.get_queryset()
        if self.request.user.user_type == CON_BOOKKEEPER:
            base_qs = self.request.user.bookkeeper.get_proxy_model().get_all_jobs()
        elif self.request.user.user_type == CON_CFO:
            base_qs = JobProxy.objects.get_queryset().filter(
                client__cfos__user=self.request.user
            )

        today = timezone.now().date()
        kpi_stats = base_qs.aggregate(
            total_jobs=Count("id", distinct=True),
            in_progress_jobs=Count(
                "id", filter=Q(status=JobStatusEnum.IN_PROGRESS), distinct=True
            ),
            past_due_jobs=Count(
                "id",
                filter=(
                    Q(status=JobStatusEnum.PAST_DUE)
                    | (
                        Q(due_date__lt=today)
                        & ~Q(status=JobStatusEnum.COMPLETED)
                        & ~Q(status=JobStatusEnum.ARCHIVED)
                    )
                ),
                distinct=True,
            ),
            need_info_jobs=Count(
                "id", filter=Q(state=JobStateEnum.NEED_INFO), distinct=True
            ),
            completed_jobs=Count(
                "id", filter=Q(status=JobStatusEnum.COMPLETED), distinct=True
            ),
        )
        context["kpi_stats"] = kpi_stats
        context.setdefault("filter_form", getattr(self.filterset, "form", None))
        context.setdefault("filter_form_id", "jobFilterForm")
        context.setdefault("table_header_subtitle", _("Jobs for all clients"))
        context.setdefault("total_records", kpi_stats.get("total_jobs", 0))
        context.setdefault(
            "extra_context", {"is_show_client": True, "is_hide_manager": False}
        )
        context.setdefault(
            "info_details",
            {
                "tooltip_txt": (
                    BW_INFO_MODAL_CSS_CLASSES.get("job").get("tooltip_txt")
                ),
                "modal_css_id": BW_INFO_MODAL_CSS_CLASSES.get("job").get("cssID"),
            },
        )
        context.setdefault("filter_categories_is_enabled", True)
        context.setdefault(
            "filter_categories",
            {
                "categories_add_form": JobCategoryForm,
                "categories_add_form_css_id": "jobCategoriesCreateForm",
                "categories_add_form_css_class": "filterCategoryForms",
                "categories_object_list": JobCategory.objects.annotate(
                    jobs_count=Count(
                        "jobs",
                        filter=Q(jobs__is_deleted=False),
                        distinct=True,
                    )
                ),
                "categories_modal_title": _("Job categories"),
                "category_app_label": "job_category",
                "is_actions_menu_enabled": False,
                "category_filter_form_action_url": reverse_lazy(
                    "dashboard:job_category:api:job-category-api-router-list"
                ),
            },
        )
        context.setdefault("visibility_filter_form", JobVisibilityForm)

        return context

    def get_queryset(self):
        show_all_jobs = self.request.GET.get("show_all_jobs")
        status_filter = self.request.GET.get("status")

        queryset = JobProxy.objects.get_queryset()

        if self.request.user.user_type == CON_BOOKKEEPER:
            if show_all_jobs:
                queryset = self.request.user.bookkeeper.get_proxy_model().get_all_jobs()
            else:
                queryset = (
                    self.request.user.bookkeeper.get_proxy_model().get_user_jobs()
                )
        elif self.request.user.user_type == CON_CFO:
            queryset = JobProxy.objects.get_queryset().filter(
                client__cfos__user=self.request.user
            )

        if not status_filter and not show_all_jobs:
            queryset = queryset.exclude(
                status__in=[CON_ARCHIVED, CON_COMPLETED, CON_DRAFT]
            )

        queryset = (
            queryset
            .select_related("client", "managed_by")
            .prefetch_related("categories")
            .annotate(
                total_tasks_count=Count("tasks", distinct=True),
                completed_tasks_count=Count(
                    "tasks", filter=Q(tasks__is_completed=True), distinct=True
                ),
                discussions_count=Count("discussions", distinct=True),
                documents_count=Count("documents", distinct=True),
            )
        )

        self.filterset = JobFilter(self.request.GET, queryset=queryset)

        return self.filterset.qs


class JobExportView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    View,
):
    """Export filtered jobs to CSV."""

    permission_required = "job.can_view_list"

    def get(self, request, *args, **kwargs):
        queryset = JobProxy.objects.get_queryset()
        if request.user.user_type == CON_BOOKKEEPER:
            queryset = request.user.bookkeeper.get_proxy_model().get_user_jobs()
        elif request.user.user_type == CON_CFO:
            queryset = JobProxy.objects.get_queryset().filter(
                client__cfos__user=request.user
            )

        queryset = (
            queryset
            .select_related("client", "managed_by")
            .prefetch_related("categories")
            .annotate(
                total_tasks_count=Count("tasks", distinct=True),
                completed_tasks_count=Count(
                    "tasks", filter=Q(tasks__is_completed=True), distinct=True
                ),
            )
        )

        filterset = JobFilter(request.GET, queryset=queryset)
        filtered_qs = filterset.qs

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="jobs_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "Job Title",
            "Client",
            "Managed By",
            "Status",
            "State",
            "Job Type",
            "Period Year",
            "Period Month",
            "Start Date",
            "Due Date",
            "Total Tasks",
            "Completed Tasks",
            "Categories",
            "Created At",
        ])

        for job_obj in filtered_qs:
            categories_str = ", ".join(c.name for c in job_obj.categories.all())
            writer.writerow([
                job_obj.title or "",
                str(job_obj.client) if job_obj.client else "No client",
                str(job_obj.managed_by) if job_obj.managed_by else "Unassigned",
                job_obj.get_status_display(),
                job_obj.get_state_display() if job_obj.state else "",
                job_obj.get_job_type_display() if job_obj.job_type else "",
                job_obj.period_year or "",
                job_obj.get_period_month_display() if job_obj.period_month else "",
                (job_obj.start_date.strftime("%Y-%m-%d") if job_obj.start_date else ""),
                (job_obj.due_date.strftime("%Y-%m-%d") if job_obj.due_date else ""),
                getattr(job_obj, "total_tasks_count", 0),
                getattr(job_obj, "completed_tasks_count", 0),
                categories_str,
                (job_obj.created_at.strftime("%Y-%m-%d") if job_obj.created_at else ""),
            ])

        return response


class JobQuickPeekView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    DetailView,
):
    """Render lightweight partial HTML for Quick Peek Slide-Over Drawer."""

    permission_required = "job.can_view_list"
    model = JobProxy
    template_name = "bw_components/job/quick_peek_content.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("client", "managed_by")
            .prefetch_related("categories", "tasks", "notes", "documents")
            .annotate(
                total_tasks_count=Count("tasks", distinct=True),
                completed_tasks_count=Count(
                    "tasks", filter=Q(tasks__is_completed=True), distinct=True
                ),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.get_object()
        context["job"] = job
        context["tasks"] = job.tasks.all()
        context["notes"] = job.notes.all()[:5]
        context["documents"] = job.documents.all()[:5]
        return context


class JobCreateView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    CreateView,
):
    # permission_required = ["job.add_job", "job.add_jobproxy"]
    permission_required = "job.add_job"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "job/create.html"
    form_class = JobForm
    success_message = _("Job created successfully")
    success_url = reverse_lazy("dashboard:job:list")

    # template_name_suffix = "_create_client"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Create job"))
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"user_type": self.request.user.user_type})
        kwargs.update({"user": self.request.user})
        return kwargs


class JobDetailsView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    DetailView,
):
    permission_required = "job.view_job"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "job/details.html"
    model = JobProxy

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _(f"Job - {self.get_object().title}"))

        job_update_form = JobForm(
            instance=self.get_object(),
            is_updated=True,
            renderer=BWFormRenderer(),
            client=self.get_object().client,
            # removed_fields=["is_scheduled"],
        )
        task_form = TaskForm(
            initial={"job": self.get_object(), "client": self.get_object().client},
            # removed_fields=["job"],
            hidden_fields=["job"],
            renderer=BWFormRenderer(),
        )
        document_form = DocumentForm(
            initial={"job": self.get_object(), "document_section": "job"},
            renderer=BWFormRenderer(),
            removed_fields=["client", "task", "status", "job"],
        )
        note_form = NoteForm(
            renderer=BWFormRenderer(),
            initial={"job": self.get_object()},
            removed_fields=["client", "task", "job"],
        )
        special_assignment_form = MiniSpecialAssignmentForm(
            initial={"assigned_by": self.request.user.pk, "job": self.get_object()}
        )
        current_user = self.request.user
        # current_user = BWUser.objects.get(pk="907c039a-b151-4faf-aed2-6c30ce4da3a9")
        discussion_initial_data = {
            "job": self.get_object(),
            # "user": self.request.user.pk,
            current_user.get_staff_member_object.get(
                "user_type"
            ): current_user.get_staff_member_object.get("staff_object"),
            "sender": self.request.user.pk,
        }
        # debugging_print(self.request.user.get_staff_member_object)
        # debugging_print(discussion_initial_data)
        discussion_form = DiscussionMiniForm(
            initial=discussion_initial_data
            # removed_fields=["special_assignment", "replies"],
        )
        context.setdefault("job_update_form", job_update_form)
        context.setdefault("job_status_choices", JobStatusEnum.choices)
        context.setdefault("job_stats_choices", JobStateEnum.choices)
        context.setdefault("task_form", task_form)
        context.setdefault("document_form", document_form)
        context.setdefault("note_form", note_form)
        context.setdefault("discussion_form", discussion_form)
        context.setdefault("special_assignment_form", special_assignment_form)
        return context

    def get_object(self, queryset=None):
        """Return the object the view is displaying.
        Require `self.queryset` and a `pk` or `slug` argument in the URLconf.
        Subclasses can override this to return any object.
        """
        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        if queryset is None:
            queryset = self.get_queryset()
        # Next, try looking up by primary key.
        pk = self.kwargs.get(self.pk_url_kwarg)
        slug = self.kwargs.get(self.slug_url_kwarg)
        if pk is not None:
            queryset = JobProxy.original_objects.filter(pk=pk)
        # Next, try looking up by slug.
        if slug is not None and (pk is None or self.query_pk_and_slug):
            slug_field = self.get_slug_field()
            queryset = queryset.filter(**{slug_field: slug})
        # If none of those are defined, it's an error.
        if pk is None and slug is None:
            raise AttributeError(
                _(
                    "Generic detail view %s must be called with either an object pk"
                    " or a slug in the URLconf." % self.__class__.__name__
                )
            )
        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": queryset.model._meta.verbose_name}
            )
        return obj


class JobUpdateView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    UpdateReturnPreviousMixin,
    UpdateView,
):
    permission_required = "job.change_job"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "job/update.html"
    form_class = JobForm
    success_message = _("Job updated successfully")
    model = JobProxy
    BASE_SUCCESS_URL = "dashboard:job:list"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Update job"))
        return context


class JobDeleteView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    SuccessMessageMixin,
    DeleteView,
):
    template_name = "core/crudl/delete.html"
    permission_required = "job.delete_job"
    permission_denied_message = _("You do not have permission to access this page.")
    model = JobProxy
    success_message = _("Job deleted successfully")
    success_url = reverse_lazy("dashboard:job:list")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Delete job"))
        context.setdefault("cancel_url", "dashboard:job:list")
        context.setdefault("object", self.get_object())
        context.setdefault("object_name", "job")
        context.setdefault("form_css_id", "deleteJobForm")

        return context
