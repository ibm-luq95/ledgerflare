# -*- coding: utf-8 -*-#
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.cache import BWSiteSettingsViewMixin
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.constants.users import CON_BOOKKEEPER, CON_CFO
from core.views.mixins import BWLoginRequiredMixin, BWBaseListViewMixin
from core.views.mixins.bookkeeper_pass_related_mixin import BookkeeperPassRelatedMixin
from core.views.mixins.update_previous_mixin import UpdateReturnPreviousMixin
from note.filters import NoteFilter
from note.forms import NoteForm
from note.models import Note


class NoteListView(
    PermissionRequiredMixin,
    UserPassesTestMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    ListView,
):
    permission_required = "note.can_view_list"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "core/crudl/list.html"
    model = Note
    paginate_by = LIST_VIEW_PAGINATE_BY
    list_type = "list"
    page_title = _("Notes")
    page_header = _("notes".title())
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
    empty_label = _("notes")
    actions_items = "update,delete"

    def test_func(self) -> bool:
        user_type = self.request.user.user_type
        if user_type != CON_CFO:
            return True

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # context.setdefault("filter_form", self.filterset.form)
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
                "tooltip_txt": BW_INFO_MODAL_CSS_CLASSES.get("note").get("tooltip_txt"),
                "modal_css_id": BW_INFO_MODAL_CSS_CLASSES.get("note").get("cssID"),
            },
        )
        context.setdefault("filter_form_id", "notesFilterForm")
        if self.request.GET:
            context["title"] = _("Filtered Notes")
        else:
            context["title"] = _("Notes")

        # debugging_print(self.filterset.form["name"])
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.user_type == CON_BOOKKEEPER:
            queryset = (
                self.request.user.bookkeeper.get_proxy_model().get_all_related_items(
                    "notes"
                )
            )
        self.filterset = NoteFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs


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

    # template_name_suffix = "_create_client"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Create note"))
        return context


class NoteUpdateView(
    PermissionRequiredMixin,
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
    # success_url = reverse_lazy("dashboard:note:list")
    model = Note
    BASE_SUCCESS_URL = "dashboard:note:list"

    # template_name_suffix = "_create_client"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Update note"))
        return context


class NoteDeleteView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    SuccessMessageMixin,
    DeleteView,
):
    template_name = "core/crudl/delete.html"
    permission_required = "note.delete_note"
    permission_denied_message = _("You do not have permission to access this page.")
    model = Note
    success_message = _("Note deleted successfully")
    success_url = reverse_lazy("dashboard:note:list")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Delete note"))
        context.setdefault("cancel_url", "dashboard:note:list")
        context.setdefault("object", self.get_object())
        context.setdefault("object_name", "note")
        context.setdefault("form_css_id", "noteDeleteForm")
        return context
