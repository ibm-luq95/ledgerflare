from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import Http404
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.cache import BWSiteSettingsViewMixin
from core.choices import JobStatusEnum, JobStateEnum
from core.config.forms import BWFormRenderer
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.constants.status_labels import CON_ARCHIVED, CON_COMPLETED, CON_DRAFT
from core.constants.users import CON_BOOKKEEPER, CON_ASSISTANT, CON_MANAGER
from core.utils.developments.debugging_print_object import DebuggingPrint
from core.views.mixins import BWLoginRequiredMixin, BWBaseListViewMixin
from core.views.mixins.update_previous_mixin import UpdateReturnPreviousMixin
from discussion.forms import DiscussionMiniForm
from document.forms import DocumentForm
from job.filters import JobFilter
from job.filters.job_visibility_form import JobVisibilityForm
from job.forms import JobForm
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
    template_name = "core/crudl/list.html"
    model = JobProxy

    paginate_by = LIST_VIEW_PAGINATE_BY
    list_type = "list"
    is_show_create_btn = True
    is_filters_enabled = True
    is_actions_menu_enabled = True
    is_header_enabled = True
    is_footer_enabled = True
    show_info_icon = True
    page_title = _("Jobs")
    page_header = _("Jobs".title())
    component_path = "bw_components/job/table_list.html"
    actions_base_url = "dashboard:job"
    filter_cancel_url = "dashboard:job:list"
    subtitle = _("jobs for all clients".title())
    pagination_list_url_name = "dashboard:job:list"
    base_url_name = "dashboard:job"
    empty_label = _("jobs")
    actions_items = "details,update,delete"

    # def paginate_queryset(self, queryset, page_size):
    #     queryset = JobProxy.objects.filter(
    #         ~Q(status__in=[CON_ARCHIVED, CON_COMPLETED, CON_DRAFT])
    #     ).order_by("title")
    #     return super().paginate_queryset(queryset, page_size)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        if self.request.GET:
            context["title"] = _("Filtered jobs")
        else:
            context["title"] = _("Jobs")

        # DebuggingPrint.pprint(dir(self.paginator_class))
        # DebuggingPrint.pprint(dir(self.paginator_class.count))
        # DebuggingPrint.log(self.paginator_class.page())
        # context.setdefault("filter_form", self.filterset.form)
        context.setdefault("filter_form_id", "jobFilterForm")
        context.setdefault("table_header_subtitle", _("Jobs subtitle"))
        context.setdefault("total_records", JobProxy.objects.count())
        context.setdefault(
            "extra_context", {"is_show_client": True, "is_hide_manager": False}
        )
        context.setdefault(
            "info_details",
            {
                "tooltip_txt": BW_INFO_MODAL_CSS_CLASSES.get("job").get("tooltip_txt"),
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
                "categories_object_list": JobCategory.objects.all(),
                "categories_modal_title": _("Job categories"),
                "category_app_label": "job_category",
                "is_actions_menu_enabled": False,
                "category_filter_form_action_url": reverse_lazy(
                    "dashboard:job_category:api:job-category-api-router-list"
                ),
            },
        )
        context.setdefault("visibility_filter_form", JobVisibilityForm)

        # debugging_print(self.filterset.form["name"])
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        show_all_jobs = self.request.GET.get("show_all_jobs")
        if show_all_jobs:
            # queryset = JobProxy.objects.filter(
            #     ~Q(status__in=[CON_ARCHIVED, CON_COMPLETED, CON_DRAFT])
            # ).order_by("title")
            queryset = JobProxy.original_objects.all()
        if self.request.user.user_type == CON_BOOKKEEPER:
            # queryset = self.request.user.bookkeeper.get_proxy_model().get_user_jobs()
            if show_all_jobs:
                queryset = self.request.user.bookkeeper.get_proxy_model().get_all_jobs()
            else:
                queryset = self.request.user.bookkeeper.get_proxy_model().get_user_jobs()

        self.filterset = JobFilter(self.request.GET, queryset=queryset)

        return self.filterset.qs


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
    UserPassesTestMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    DetailView,
):
    # permission_required = ["job.view_job", "job.view_jobproxy"]
    permission_required = "job.view_job"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "job/details.html"
    model = JobProxy

    # template_name_suffix = "_create_client"

    def test_func(self) -> bool:
        user = self.request.user
        if user.user_type == CON_ASSISTANT or user.user_type == CON_MANAGER:
            return True
        else:
            return self.get_object().managed_by == user

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
            initial={"assigned_by": self.request.user.pk, "job": self.get_object().pk}
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
            initial=discussion_initial_data,
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
        """
        Return the object the view is displaying.
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
                    "Generic detail view %s must be called with either an object pk or a slug in the URLconf."
                    % self.__class__.__name__
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
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    UpdateReturnPreviousMixin,
    UpdateView,
):
    # permission_required = ["job.change_job", "job.change_jobproxy"]
    permission_required = "job.change_job"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "job/update.html"
    form_class = JobForm
    success_message = _("Job updated successfully")
    # success_url = reverse_lazy("dashboard:job:list")
    model = JobProxy
    BASE_SUCCESS_URL = "dashboard:job:list"

    # template_name_suffix = "_create_client"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Update job"))
        return context


class JobDeleteView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    SuccessMessageMixin,
    DeleteView,
):
    template_name = "core/crudl/delete.html"
    # permission_required = ["job.delete_job", "job.delete_jobproxy"]
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
