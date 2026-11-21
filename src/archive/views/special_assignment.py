# -*- coding: utf-8 -*-#
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.translation import gettext as _
from django.views.generic import ListView

from core.cache import BWSiteSettingsViewMixin
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.constants.users import CON_BOOKKEEPER
from core.views.mixins import BWLoginRequiredMixin, BWBaseListViewMixin
from special_assignment.filters import SpecialAssignmentFilter
from special_assignment.models import SpecialAssignmentProxy


class SpecialAssignmentArchiveListView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    ListView,
):
    permission_required = "special_assignment.can_view_list"
    template_name = "core/crudl/list.html"
    model = SpecialAssignmentProxy
    paginate_by = LIST_VIEW_PAGINATE_BY
    list_type = "archive"
    queryset = SpecialAssignmentProxy.archive_objects.all()
    is_show_create_btn = False
    is_filters_enabled = True
    is_actions_menu_enabled = True
    is_header_enabled = True
    is_footer_enabled = True
    show_info_icon = False
    page_title = _("Special assignments archive")
    page_header = _("Special assignments archive".title())
    component_path = "bw_components/special_assignment/table_list.html"
    actions_base_url = "dashboard:special_assignment"
    filter_cancel_url = "dashboard:archive:special_assignment:list"
    table_header_title = _("C")
    pagination_list_url_name = "dashboard:archive:special_assignment:list"
    base_url_name = "dashboard:special_assignment"
    empty_label = _("assignment(s)")
    subtitle = _(
        "Completed and archived special assignments, closed investigations, and past deliverables."
    )
    actions_items = "details,update,delete"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # context.setdefault("filter_form", self.filterset.form)
        context.setdefault("extra_context", {})
        context.setdefault(
            "info_details",
            {
                "tooltip_txt": BW_INFO_MODAL_CSS_CLASSES.get("special_assignment").get(
                    "tooltip_txt"
                ),
                "modal_css_id": BW_INFO_MODAL_CSS_CLASSES.get("special_assignment").get(
                    "cssID"
                ),
            },
        )

        # debugging_print(self.filterset.form["name"])
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.user_type == CON_BOOKKEEPER:
            queryset = (
                self.request.user.bookkeeper.get_proxy_model().special_assignments.all()
            )
        self.filterset = SpecialAssignmentFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs
