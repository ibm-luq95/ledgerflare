from __future__ import annotations

from datetime import timedelta
from typing import Any

from core.constants.identity import LedgerFlareIdentity
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q, QuerySet
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from core.cache import BWSiteSettingsViewMixin
from core.choices import NoteSectionEnum
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.constants.users import CON_ASSISTANT, CON_BOOKKEEPER, CON_CFO, CON_MANAGER
from core.views.mixins import (
    BWBaseListViewMixin,
    BWLoginRequiredMixin,
    BWObjectAccessRequiredMixin,
)
from core.views.mixins.bookkeeper_pass_related_mixin import BookkeeperPassRelatedMixin
from core.views.mixins.update_previous_mixin import UpdateReturnPreviousMixin
from note.filters import NoteFilter
from note.forms import NoteForm
from note.models import NoteProxy


class NoteListView(
    PermissionRequiredMixin,
    UserPassesTestMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    ListView,
):
    """Refactored Note list view with KPI stats and query optimization."""

    permission_required = "note.can_view_list"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "note/list.html"
    model = NoteProxy
    paginate_by = LIST_VIEW_PAGINATE_BY
    list_type = "list"
    page_title = _("Notes")
    page_header = _("Notes")
    component_path = "bw_components/note/table_list.html"
    actions_base_url = "dashboard:note"
    filter_cancel_url = "dashboard:note:list"
    is_show_create_btn = True
    is_filters_enabled = True
    is_actions_menu_enabled = True
    is_header_enabled = True
    is_footer_enabled = True
    show_info_icon = False
    pagination_list_url_name = "dashboard:note:list"
    base_url_name = "dashboard:note"
    empty_label = _("note")
    actions_items = "update,delete"
    subtitle = _(
        "Centralized audit notes, internal comments, and client engagement annotations."
    )

    def test_func(self) -> bool:
        user_type = getattr(self.request.user, "user_type", None)
        return user_type != CON_CFO

    def get_scoped_base_queryset(self) -> QuerySet[NoteProxy]:
        """Return base role-scoped queryset before filtering."""
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        if user.is_superuser or getattr(user, "user_type", None) in (
            CON_MANAGER,
            CON_CFO,
        ):
            return queryset

        if getattr(user, "user_type", None) == CON_BOOKKEEPER and hasattr(
            user, "bookkeeper"
        ):
            return user.bookkeeper.get_proxy_model().get_all_related_items("notes")
        if getattr(user, "user_type", None) == CON_ASSISTANT and hasattr(
            user, "assistant"
        ):
            return user.assistant.get_proxy_model().get_all_related_items("notes")
        return queryset

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Inject aggregate KPI metrics, filter forms, and configuration context."""
        context = super().get_context_data(**kwargs)
        base_qs = self.get_scoped_base_queryset()
        seven_days_ago = timezone.now() - timedelta(days=7)

        kpi_stats = base_qs.aggregate(
            total_notes=Count("id", distinct=True),
            client_notes=Count(
                "id",
                filter=Q(note_section=NoteSectionEnum.CLIENT),
                distinct=True,
            ),
            job_notes=Count(
                "id",
                filter=Q(note_section=NoteSectionEnum.JOB),
                distinct=True,
            ),
            task_notes=Count(
                "id",
                filter=Q(note_section=NoteSectionEnum.TASK),
                distinct=True,
            ),
            recent_notes=Count(
                "id",
                filter=Q(created_at__gte=seven_days_ago),
                distinct=True,
            ),
        )
        context["kpi_stats"] = kpi_stats
        context["total_records"] = kpi_stats.get("total_notes", 0)

        filter_form = getattr(self, "filterset", None) and self.filterset.form
        if filter_form is None:
            filter_form = NoteFilter(self.request.GET, queryset=base_qs).form
        context["filter_form"] = filter_form
        context.setdefault("filter_form_id", "notesFilterForm")
        context.setdefault(
            "extra_context",
            {
                "is_show_section": True,
                "is_show_job_link": True,
                "is_show_client_link": True,
                "is_show_task_link": True,
            },
        )
        context.setdefault(
            "info_details",
            {
                "tooltip_txt": BW_INFO_MODAL_CSS_CLASSES.get("note", {}).get(
                    "tooltip_txt", ""
                ),
                "modal_css_id": BW_INFO_MODAL_CSS_CLASSES.get("note", {}).get(
                    "cssID", ""
                ),
            },
        )
        if self.request.GET:
            context["title"] = _("Filtered Notes")
        else:
            context["title"] = _("Notes")

        return context

    def get_queryset(self) -> QuerySet[NoteProxy]:
        """Return eager-loaded filtered notes queryset avoiding N+1 queries."""
        queryset = self.get_scoped_base_queryset()
        queryset = queryset.select_related("client", "job", "task")
        self.filterset = NoteFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs


class NoteQuickPeekView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    DetailView,
):
    """Render lightweight partial HTML for Quick Peek Slide-Over Drawer."""

    permission_required = "note.can_view_list"
    model = NoteProxy
    template_name = "bw_components/note/quick_peek_content.html"

    def get_queryset(self) -> QuerySet[NoteProxy]:
        return super().get_queryset().select_related("client", "job", "task")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["today"] = timezone.now().date()
        return context


class BaseNoteExportView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    View,
):
    """Base class for exporting filtered notes."""

    permission_required = "note.can_view_list"
    permission_denied_message = _("You do not have permission to export notes.")

    def get_queryset(self) -> QuerySet[NoteProxy]:
        """Return eager-loaded filtered notes matching query params."""
        view_instance = NoteListView()
        view_instance.request = self.request
        base_qs = view_instance.get_scoped_base_queryset()
        base_qs = base_qs.select_related("client", "job", "task")
        filterset = NoteFilter(self.request.GET, queryset=base_qs)
        return filterset.qs


class NoteExportCsvView(BaseNoteExportView):
    """View to export notes to CSV format."""

    def get(self, request: Any, *args: Any, **kwargs: Any) -> HttpResponse:
        notes = self.get_queryset()
        from note.services import NoteExportService

        service = NoteExportService()
        return service.export_csv(notes)


class NoteExportExcelView(BaseNoteExportView):
    """View to export notes to XLSX format."""

    def get(self, request: Any, *args: Any, **kwargs: Any) -> HttpResponse:
        notes = self.get_queryset()
        from note.services import NoteExportService

        service = NoteExportService()
        return service.export_xlsx(notes)


class NoteExportView(BaseNoteExportView):
    """Unified view to export notes based on format param ('csv' or 'xlsx')."""

    def get(self, request: Any, *args: Any, **kwargs: Any) -> HttpResponse:
        notes = self.get_queryset()
        export_format = request.GET.get("format", "csv").lower()
        from note.services import NoteExportService

        service = NoteExportService()
        if export_format in ["xlsx", "excel"]:
            return service.export_xlsx(notes)
        return service.export_csv(notes)


class NoteCreateView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    BookkeeperPassRelatedMixin,
    CreateView,
):
    permission_required = "note.add_note"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "note/create.html"
    form_class = NoteForm
    success_message = _("Note created successfully")
    success_url = reverse_lazy("dashboard:note:list")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Create note"))
        return context


class NoteUpdateView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    BookkeeperPassRelatedMixin,
    UpdateReturnPreviousMixin,
    UpdateView,
):
    permission_required = "note.change_note"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "note/update.html"
    form_class = NoteForm
    success_message = _("Note updated successfully")
    model = NoteProxy
    BASE_SUCCESS_URL = "dashboard:note:list"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Update note"))
        return context


class NoteDeleteView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    SuccessMessageMixin,
    DeleteView,
):
    template_name = "core/crudl/delete.html"
    permission_required = "note.delete_note"
    permission_denied_message = _("You do not have permission to access this page.")
    model = NoteProxy
    success_message = _("Note deleted successfully")
    success_url = reverse_lazy("dashboard:note:list")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Delete note"))
        context.setdefault("cancel_url", "dashboard:note:list")
        context.setdefault("object", self.get_object())
        context.setdefault("object_name", "note")
        context.setdefault("form_css_id", "noteDeleteForm")
        return context
