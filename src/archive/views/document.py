# -*- coding: utf-8 -*-#
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView

from core.cache import BWSiteSettingsViewMixin
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.constants.users import CON_BOOKKEEPER, CON_CFO
from django.utils.translation import gettext as _

from core.views.mixins import BWLoginRequiredMixin, BWBaseListViewMixin
from document.filters import DocumentFilter
from document.models import Document, DocumentProxy


class DocumentArchiveListView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    ListView,
):
    permission_required = "document.can_view_list"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "core/crudl/list.html"
    model = Document
    # queryset = Client.objects.filter(~Q(status="archive")).prefetch_related("jobs")
    # queryset = Client.objects.prefetch_related(
    #     "jobs", "jobs__created_by", "important_contacts"
    # ).filter(~Q(status=CON_ARCHIVED))
    paginate_by = LIST_VIEW_PAGINATE_BY
    list_type = "archive"
    is_show_create_btn = False
    is_filters_enabled = True
    is_actions_menu_enabled = True
    is_header_enabled = True
    is_footer_enabled = True
    show_info_icon = False
    page_title = _("Documents archive")
    page_header = _("Documents archive".title())
    component_path = "bw_components/document/table_list.html"
    actions_base_url = "dashboard:document"
    filter_cancel_url = "dashboard:archive:documents:list"
    table_header_title = _("C")
    pagination_list_url_name = "dashboard:archive:documents:list"
    base_url_name = "dashboard:document"
    empty_label = _("document(s)")
    subtitle = _(
        "Archived financial documents, past period workpapers, and historical attachments."
    )
    actions_items = "update,delete"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # context.setdefault("filter_form", self.filterset.form)
        context.setdefault("extra_context", {})
        context.setdefault(
            "info_details",
            {
                "tooltip_txt": BW_INFO_MODAL_CSS_CLASSES.get("document").get(
                    "tooltip_txt"
                ),
                "modal_css_id": BW_INFO_MODAL_CSS_CLASSES.get("document").get("cssID"),
            },
        )

        # debugging_print(self.filterset.form["name"])
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.user_type == CON_BOOKKEEPER:
            queryset = (
                self.request.user.bookkeeper.get_proxy_model().get_all_related_items(
                    "documents", is_archived=True
                )
            )
        elif self.request.user.user_type == CON_CFO:
            queryset = DocumentProxy.archive_objects.filter(
                client__cfos__user=self.request.user
            )
        self.filterset = DocumentFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs
