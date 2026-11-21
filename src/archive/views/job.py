# -*- coding: utf-8 -*-#
from django.utils.translation import gettext as _
from django.views.generic import (
    ListView,
)

from core.cache import BWSiteSettingsViewMixin
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.users import CON_BOOKKEEPER, CON_CFO
from core.views.mixins import BWLoginRequiredMixin, BWBaseListViewMixin
from job.filters import JobFilter
from job.models import JobProxy


class JobArchiveListView(
    BWLoginRequiredMixin, BWSiteSettingsViewMixin, BWBaseListViewMixin, ListView
):
    template_name = "core/crudl/list.html"
    model = JobProxy
    paginate_by = LIST_VIEW_PAGINATE_BY
    list_type = "archive"
    queryset = JobProxy.archive_objects.all()
    is_show_create_btn = False
    is_filters_enabled = True
    is_actions_menu_enabled = True
    is_header_enabled = True
    is_footer_enabled = True
    show_info_icon = False
    page_title = _("Jobs archive")
    page_header = _("Jobs archive".title())
    component_path = "bw_components/archive/job/table_list.html"
    actions_base_url = "dashboard:jobs"
    filter_cancel_url = "dashboard:archive:jobs:list"
    table_header_title = _("C")
    pagination_list_url_name = "dashboard:archive:jobs:list"
    base_url_name = "dashboard:job"
    empty_label = _("job(s)")
    subtitle = _(
        "Completed and archived fiscal jobs, past reconciliation periods, and closed engagements."
    )

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)

        # context.setdefault("filter_form", self.filterset.form)
        # context.setdefault("base_url_name", "dashboard:job")
        context.setdefault("extra_context", {"is_show_client": True})
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.user_type == CON_BOOKKEEPER:
            queryset = self.request.user.bookkeeper.get_proxy_model().get_user_jobs(
                is_archived=True
            )
        elif self.request.user.user_type == CON_CFO:
            queryset = JobProxy.archive_objects.filter(
                client__cfos__user=self.request.user
            )
        self.filterset = JobFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs
