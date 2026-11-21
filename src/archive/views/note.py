# -*- coding: utf-8 -*-#
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView

from core.cache import BWSiteSettingsViewMixin
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.constants.users import CON_BOOKKEEPER, CON_CFO
from core.views.mixins import BWBaseListViewMixin, BWLoginRequiredMixin
from note.filters import NoteFilter
from django.utils.translation import gettext as _

from note.models import Note


class NoteArchiveListView(
    PermissionRequiredMixin,
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
    list_type = "archive"
    queryset = Note.archive_objects.all()
    is_show_create_btn = False
    is_filters_enabled = True
    is_actions_menu_enabled = True
    is_header_enabled = True
    is_footer_enabled = True
    show_info_icon = False
    page_title = _("Notes archive")
    page_header = _("Notes archive".title())
    component_path = "bw_components/note/table_list.html"
    actions_base_url = "dashboard:note"
    filter_cancel_url = "dashboard:archive:notes:list"
    pagination_list_url_name = "dashboard:archive:notes:list"
    base_url_name = "dashboard:note"
    empty_label = _("note(s)")
    subtitle = _(
        "Archived internal annotations, legacy comments, and historical client notes."
    )
    actions_items = "update,delete"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # context.setdefault("filter_form", self.filterset.form)
        context.setdefault("extra_context", {"is_show_section": True})

        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.user_type == CON_BOOKKEEPER:
            queryset = (
                self.request.user.bookkeeper.get_proxy_model().get_all_related_items(
                    "notes"
                )
            )
        elif self.request.user.user_type == CON_CFO:
            queryset = NoteProxy.archive_objects.filter(
                client__cfos__user=self.request.user
            )
        self.filterset = NoteFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs
