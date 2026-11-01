# -*- coding: utf-8 -*-#
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import ListView, UpdateView, CreateView, DeleteView

from core.cache import BWSiteSettingsViewMixin
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.views.mixins import BWLoginRequiredMixin, BWBaseListViewMixin
from core.views.mixins.bookkeeper_pass_related_mixin import BookkeeperPassRelatedMixin
from core.views.mixins.update_previous_mixin import UpdateReturnPreviousMixin
from staff_briefcase.filters import StaffNotesFilter
from staff_briefcase.forms.notes import StaffNotesForm
from staff_briefcase.models import StaffNotes


class StaffNotesListView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    ListView,
):
    permission_required = "staff_briefcase.staffnotes.can_view_list"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "core/crudl/list.html"
    model = StaffNotes
    paginate_by = LIST_VIEW_PAGINATE_BY
    list_type = "list"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context["title"] = _("Staff Notes")
        context.setdefault("filter_form", self.filterset.form)
        context.setdefault("list_type", self.list_type)
        context.setdefault("page_header", _("staff notes".title()))
        context.setdefault(
            "component_path", "bw_components/staff_briefcase/notes/table_list.html"
        )
        context.setdefault(
            "subtitle",
            _(
                "Private memos, working references, and operational reminders for staff members."
            ),
        )
        context.setdefault(
            "actions_base_url", "dashboard:briefcase:briefcase_staff_notes"
        )
        context.setdefault(
            "filter_cancel_url", "dashboard:briefcase:briefcase_staff_notes:list"
        )
        context.setdefault("table_header_title", _("C"))
        context.setdefault(
            "table_header_subtitle",
            _("Personal work notes, draft summaries, and internal reminders."),
        )
        context.setdefault("is_show_create_btn", True)
        context.setdefault(
            "pagination_list_url_name", "dashboard:briefcase:briefcase_staff_notes:list"
        )
        context.setdefault("is_filters_enabled", True)
        context.setdefault("is_actions_menu_enabled", True)
        context.setdefault("is_header_enabled", True)
        context.setdefault("is_footer_enabled", True)
        context.setdefault("actions_items", "update,delete")
        context.setdefault("base_url_name", "dashboard:briefcase:briefcase_staff_notes")
        context.setdefault("empty_label", _("staff notes".capitalize()))
        context.setdefault(
            "extra_context",
            {
                "is_show_briefcase": True,
            },
        )
        context.setdefault("show_info_icon", True)
        context.setdefault(
            "info_details",
            {
                "tooltip_txt": BW_INFO_MODAL_CSS_CLASSES.get("note").get("tooltip_txt"),
                "modal_css_id": BW_INFO_MODAL_CSS_CLASSES.get("note").get("cssID"),
            },
        )

        # debugging_print(self.filterset.form["name"])
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_superuser:
            queryset = queryset.filter(briefcase__user=user)
        self.filterset = StaffNotesFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs


class StaffNotesUpdateView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    BookkeeperPassRelatedMixin,
    UpdateReturnPreviousMixin,
    UpdateView,
):
    permission_required = "staff_briefcase.staffnotes.change_staffnotes"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "staff_briefcase/notes/update.html"
    form_class = StaffNotesForm
    success_message = _("Staff note updated successfully")
    # success_url = reverse_lazy("dashboard:note:list")
    model = StaffNotes
    BASE_SUCCESS_URL = "dashboard:briefcase:briefcase_staff_notes:list"

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(briefcase__user=self.request.user)
        return queryset

    # template_name_suffix = "_create_client"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Update staff note"))
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"is_update_view": True})
        # kwargs.update({"hidden_inputs": {"field_names": ["briefcase"]}})
        return kwargs


class StaffNotesCreateView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    CreateView,
):
    permission_required = "staff_briefcase.staffnotes.add_staffnotes"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "core/crudl/create.html"
    form_class = StaffNotesForm
    success_message = _("Staff note created successfully")
    success_url = reverse_lazy("dashboard:briefcase:briefcase_staff_notes:list")

    # template_name_suffix = "_create_client"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Create staff note"))
        context.update({
            "form_css_id": "mainStaffNotesCreateForm",
            "form_title": _("Create new staff note"),
            "form_subtitle": _("Subtitle"),
        })
        return context


class StaffNotesDeleteView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    SuccessMessageMixin,
    DeleteView,
):
    template_name = "core/crudl/delete.html"
    permission_required = "staff_briefcase.staffnotes.delete_staffnotes"
    permission_denied_message = _("You do not have permission to access this page.")
    model = StaffNotes
    success_message = _("Staff note deleted successfully")
    success_url = reverse_lazy("dashboard:briefcase:briefcase_staff_notes:list")

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(briefcase__user=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Delete note"))
        context.setdefault(
            "cancel_url", "dashboard:briefcase:briefcase_staff_notes:list"
        )
        context.setdefault("object", self.get_object())
        context.setdefault("object_name", "staff note")
        context.setdefault("form_css_id", "staffNoteDeleteForm")
        return context
