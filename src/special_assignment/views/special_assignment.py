# -*- coding: utf-8 -*-#
from __future__ import annotations

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.http import HttpResponse
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from core.cache import BWSiteSettingsViewMixin
from core.choices.special_assignment import SpecialAssignmentStatusEnum
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.constants.identity import LedgerFlareIdentity
from core.constants.status_labels import CON_ARCHIVED, CON_COMPLETED
from core.constants.users import CON_ASSISTANT, CON_BOOKKEEPER, CON_CFO, CON_MANAGER
from core.utils.developments.debugging_print_object import DebuggingPrint
from core.views.mixins import (
    BWBaseListViewMixin,
    BWLoginRequiredMixin,
    BWObjectAccessRequiredMixin,
)
from core.views.mixins.update_previous_mixin import UpdateReturnPreviousMixin
from special_assignment.filters import SpecialAssignmentFilter
from special_assignment.forms import SpecialAssignmentForm
from special_assignment.models import SpecialAssignmentProxy


class SpecialAssignmentListView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    ListView,
):
    permission_required = "special_assignment.can_view_list"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "special_assignment/list.html"
    model = SpecialAssignmentProxy
    paginate_by = LIST_VIEW_PAGINATE_BY
    list_type = "list"
    is_show_create_btn = True
    is_filters_enabled = True
    is_actions_menu_enabled = True
    is_header_enabled = True
    is_footer_enabled = True
    show_info_icon = False
    page_title = _("Special assignments")
    page_header = _("Special assignments".title())
    component_path = "bw_components/special_assignment/table_list.html"
    actions_base_url = "dashboard:special_assignment"
    filter_cancel_url = "dashboard:special_assignment:list"
    table_header_title = _("Special Assignments")
    pagination_list_url_name = "dashboard:special_assignment:list"
    actions_items = "details,update,delete"
    base_url_name = "dashboard:special_assignment"
    empty_label = _("special assignment")
    subtitle = _(
        "Ad-hoc financial investigations, urgent compliance tasks, and specialized client requests."
    )

    def get_scoped_base_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if user.is_superuser or getattr(user, "user_type", None) in (
            CON_MANAGER,
            CON_CFO,
        ):
            return queryset

        if getattr(user, "user_type", None) == CON_BOOKKEEPER:
            if hasattr(user, "bookkeeper"):
                bookkeeper_proxy = user.bookkeeper.get_proxy_model()
                bookkeeper_clients = bookkeeper_proxy.clients.all()
                q_filter = (
                    Q(client__in=bookkeeper_clients)
                    | Q(assigned_to=user)
                    | Q(assigned_by=user)
                    | Q(bookkeeper=bookkeeper_proxy)
                )
                queryset = queryset.filter(q_filter).distinct()
            else:
                queryset = queryset.filter(
                    Q(assigned_to=user) | Q(assigned_by=user)
                ).distinct()
        elif getattr(user, "user_type", None) == CON_ASSISTANT:
            if hasattr(user, "assistant"):
                assistant_proxy = user.assistant.get_proxy_model()
                q_filter = (
                    Q(assigned_to=user)
                    | Q(assigned_by=user)
                    | Q(assistant=assistant_proxy)
                )
                queryset = queryset.filter(q_filter).distinct()
            else:
                queryset = queryset.filter(
                    Q(assigned_to=user) | Q(assigned_by=user)
                ).distinct()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_qs = self.get_scoped_base_queryset()
        today = timezone.now().date()

        kpi_stats = base_qs.aggregate(
            total_assignments=Count("id", distinct=True),
            in_progress=Count(
                "id",
                filter=Q(status=SpecialAssignmentStatusEnum.IN_PROGRESS),
                distinct=True,
            ),
            overdue=Count(
                "id",
                filter=Q(
                    due_date__lt=today,
                    status__in=[
                        SpecialAssignmentStatusEnum.NOT_STARTED,
                        SpecialAssignmentStatusEnum.IN_PROGRESS,
                    ],
                ),
                distinct=True,
            ),
            completed=Count(
                "id",
                filter=Q(status=SpecialAssignmentStatusEnum.COMPLETED),
                distinct=True,
            ),
            unseen=Count(
                "id",
                filter=Q(is_seen=False),
                distinct=True,
            ),
        )
        context["kpi_stats"] = kpi_stats
        context["total_records"] = kpi_stats.get("total_assignments", 0)
        filter_form = getattr(self, "filterset", None) and self.filterset.form
        if filter_form is None:
            filter_form = SpecialAssignmentFilter(
                self.request.GET, queryset=base_qs
            ).form
        context["filter_form"] = filter_form
        context.setdefault("filter_form_id", "specialAssignmentsFilterForm")
        context.setdefault("extra_context", {})
        context.setdefault(
            "info_details",
            {
                "tooltip_txt": (
                    BW_INFO_MODAL_CSS_CLASSES.get("special_assignment", {}).get(
                        "tooltip_txt", ""
                    )
                ),
                "modal_css_id": (
                    BW_INFO_MODAL_CSS_CLASSES.get("special_assignment", {}).get(
                        "cssID", ""
                    )
                ),
            },
        )
        if self.request.GET:
            context["title"] = _("Filtered Special assignments")
        else:
            context["title"] = _("Special assignments")

        return context

    def get_queryset(self):
        queryset = self.get_scoped_base_queryset()
        queryset = queryset.select_related(
            "client",
            "job",
            "assigned_by",
            "assigned_to",
            "bookkeeper",
            "assistant",
            "manager",
        ).annotate(discussions_count=Count("discussions", distinct=True))
        self.filterset = SpecialAssignmentFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs


class SpecialAssignmentCreateView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    CreateView,
):
    permission_required = "special_assignment.add_specialassignment"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "special_assignment/create.html"
    form_class = SpecialAssignmentForm
    success_message = _("Special assignment created successfully")
    success_url = reverse_lazy("dashboard:special_assignment:list")

    # template_name_suffix = "_create_client"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Create assignment"))
        return context

    def get_initial(self) -> dict:
        initial = super().get_initial()
        initial.setdefault("assigned_by", self.request.user)

        return initial


class SpecialAssignmentUpdateView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    UpdateReturnPreviousMixin,
    UpdateView,
):
    permission_required = "special_assignment.change_specialassignment"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "special_assignment/update.html"
    form_class = SpecialAssignmentForm
    success_message = _("Special assignment updated successfully")
    # success_url = reverse_lazy("dashboard:special_assignment:list")
    model = SpecialAssignmentProxy
    BASE_SUCCESS_URL = "dashboard:special_assignment:list"

    # template_name_suffix = "_create_client"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Update special assignment"))

        return context


class SpecialAssignmentDeleteView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    DeleteView,
):
    permission_required = "special_assignment.delete_specialassignment"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "core/crudl/delete.html"
    model = SpecialAssignmentProxy
    success_message = _("Special assignment deleted successfully")
    success_url = reverse_lazy("dashboard:special_assignment:list")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Delete special assignment"))
        context.setdefault("cancel_url", "dashboard:special_assignment:list")
        context.setdefault("object", self.get_object())
        context.setdefault("object_name", "special assignment")
        context.setdefault("form_css_id", "specialAssignmentDeleteForm")
        return context


class SpecialAssignmentDetailsView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    DetailView,
):
    permission_required = "special_assignment.view_specialassignment"
    permission_denied_message = _("You do not have permission to access this page.")
    model = SpecialAssignmentProxy
    template_name = "special_assignment/details.html"

    def get_queryset(self):
        return SpecialAssignmentProxy.objects.all()

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("SA - ") + self.get_object().title)
        return context


class RequestedSpecialAssignmentsListView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    ListView,
):
    permission_required = "special_assignment.can_view_list"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "core/crudl/list.html"

    model = SpecialAssignmentProxy
    http_method_names = ["get"]

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("All requested special assignment"))
        context.setdefault("page_header", "requestes assignments".capitalize())
        context.setdefault("filter_form", self.filterset.form)
        context.setdefault("filter_form", self.filterset.form)
        context.setdefault("page_header", _("requestes assignments".capitalize()))
        context.setdefault(
            "component_path", "bw_components/special_assignment/table_list.html"
        )
        context.setdefault(
            "subtitle",
            _("Special assignments custom specific assignments to clients".title()),
        )
        context.setdefault("actions_base_url", "dashboard:special_assignment")
        context.setdefault("filter_cancel_url", "dashboard:special_assignment:list")
        context.setdefault("table_header_title", _("C"))
        context.setdefault("table_header_subtitle", _("Jobs subtitle"))
        context.setdefault("is_show_create_btn", True)
        context.setdefault(
            "pagination_list_url_name", "dashboard:special_assignment:list"
        )
        context.setdefault("is_filters_enabled", True)
        context.setdefault("is_actions_menu_enabled", True)
        context.setdefault("is_header_enabled", True)
        context.setdefault("is_footer_enabled", True)
        context.setdefault("actions_items", "details,update,delete")
        context.setdefault("base_url_name", "dashboard:special_assignment")
        context.setdefault("empty_label", _("assignments"))
        context.setdefault("extra_context", {})
        context.setdefault("show_info_icon", True)
        context.setdefault(
            "info_details",
            {
                "tooltip_txt": (
                    BW_INFO_MODAL_CSS_CLASSES.get("requested_assignment").get(
                        "tooltip_txt"
                    )
                ),
                "modal_css_id": (
                    BW_INFO_MODAL_CSS_CLASSES.get("requested_assignment").get("cssID")
                ),
            },
        )
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        current_user = self.request.user
        manager = None
        if hasattr(current_user, "manager"):
            manager = self.request.user.manager
        elif hasattr(current_user, "bookkeeper"):
            manager = self.request.user.bookkeeper
        elif hasattr(current_user, "assistant"):
            manager = self.request.user.assistant
        queryset = manager.user.requested_assignments.filter(
            ~Q(status__in=[CON_ARCHIVED, CON_COMPLETED])
        )
        self.filterset = SpecialAssignmentFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs


class SpecialAssignmentQuickPeekView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    DetailView,
):
    """Render lightweight partial HTML for Quick Peek Slide-Over Drawer."""

    permission_required = "special_assignment.can_view_list"
    model = SpecialAssignmentProxy
    template_name = "bw_components/special_assignment/quick_peek_content.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "client",
                "job",
                "assigned_by",
                "assigned_to",
                "bookkeeper",
                "assistant",
                "manager",
            )
            .prefetch_related("discussions")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignment = self.object
        context["recent_discussions"] = assignment.discussions.select_related(
            "sender"
        ).order_by("-created_at")[:5]
        context["today"] = timezone.now().date()
        return context


class BaseSpecialAssignmentExportView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    View,
):
    """Base class for exporting filtered special assignments."""

    permission_required = "special_assignment.can_view_list"
    permission_denied_message = _(
        "You do not have permission to export special assignments."
    )

    def get_queryset(self):
        """Return eager-loaded filtered special assignments matching query params."""
        view_instance = SpecialAssignmentListView()
        view_instance.request = self.request
        base_qs = view_instance.get_scoped_base_queryset()
        base_qs = base_qs.select_related(
            "client",
            "job",
            "assigned_by",
            "assigned_to",
            "bookkeeper",
            "assistant",
            "manager",
        )
        filterset = SpecialAssignmentFilter(self.request.GET, queryset=base_qs)
        return filterset.qs


class SpecialAssignmentExportCsvView(BaseSpecialAssignmentExportView):
    """View to export special assignments to CSV format."""

    def get(self, request, *args, **kwargs) -> HttpResponse:
        assignments = self.get_queryset()
        from special_assignment.services import SpecialAssignmentExportService

        service = SpecialAssignmentExportService()
        return service.export_csv(assignments)


class SpecialAssignmentExportExcelView(BaseSpecialAssignmentExportView):
    """View to export special assignments to XLSX format."""

    def get(self, request, *args, **kwargs) -> HttpResponse:
        assignments = self.get_queryset()
        from special_assignment.services import SpecialAssignmentExportService

        service = SpecialAssignmentExportService()
        return service.export_xlsx(assignments)


class SpecialAssignmentExportView(BaseSpecialAssignmentExportView):
    """Unified view to export special assignments based on format param."""

    def get(self, request, *args, **kwargs) -> HttpResponse:
        assignments = self.get_queryset()
        export_format = request.GET.get("format", "csv").lower()
        from special_assignment.services import SpecialAssignmentExportService

        service = SpecialAssignmentExportService()
        if export_format in ["xlsx", "excel"]:
            return service.export_xlsx(assignments)
        return service.export_csv(assignments)
