from __future__ import annotations

from typing import Any

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DetailView, ListView

from core.cache import BWSiteSettingsViewMixin
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.constants.users import CON_ASSISTANT, CON_MANAGER
from core.views.mixins import (
    BWBaseListViewMixin,
    BWLoginRequiredMixin,
    BWManagerAssistantAccessMixin,
    BWObjectAccessRequiredMixin,
)
from staff_briefcase.forms import (
    BriefcaseAccountMiniForm,
    BriefcaseDocumentMiniForm,
    BriefcaseNoteMiniForm,
)
from staff_briefcase.models import StaffBriefcase


class StaffBriefcaseListView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    ListView,
):
    permission_required = "staff_briefcase.can_view_list"
    template_name = "core/crudl/list.html"
    model = StaffBriefcase
    paginate_by = LIST_VIEW_PAGINATE_BY
    list_type = "list"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = _("Staff Briefcases")
        context.setdefault("list_type", self.list_type)
        context.setdefault("page_header", _("Briefcases".title()))
        context.setdefault(
            "component_path", "bw_components/staff_briefcase/table_list.html"
        )
        context.setdefault(
            "subtitle",
            _(
                "Personal staff workspace, private working notes, and assigned engagement references."
            ),
        )
        context.setdefault("actions_base_url", "dashboard:briefcase")
        context.setdefault("filter_cancel_url", "dashboard:special_assignment:list")
        context.setdefault("table_header_title", _("C"))
        context.setdefault(
            "table_header_subtitle",
            _("Personal briefcase items, workspace notes, and quick references."),
        )
        context.setdefault("is_show_create_btn", True)
        context.setdefault("pagination_list_url_name", "dashboard:briefcase:list")
        context.setdefault("is_filters_enabled", False)
        context.setdefault("is_actions_menu_enabled", True)
        context.setdefault("is_header_enabled", True)
        context.setdefault("is_footer_enabled", True)
        context.setdefault("actions_items", "details,")
        context.setdefault("base_url_name", "dashboard:briefcase")
        context.setdefault("empty_label", _("briefcases"))
        context.setdefault("extra_context", {})
        context.setdefault("show_info_icon", True)
        context.setdefault(
            "info_details",
            {
                "tooltip_txt": BW_INFO_MODAL_CSS_CLASSES.get("staff_briefcase").get(
                    "tooltip_txt"
                ),
                "modal_css_id": BW_INFO_MODAL_CSS_CLASSES.get("staff_briefcase").get(
                    "cssID"
                ),
            },
        )
        context.setdefault("filter_form_id", "staffBriefcaseFilterForm")
        return context

    def get_queryset(self) -> QuerySet[StaffBriefcase]:
        user = self.request.user
        if user.is_superuser or user.user_type in (CON_MANAGER, CON_ASSISTANT):
            return super().get_queryset()
        return StaffBriefcase.objects.filter(user=user)


class StaffBriefcaseDetailView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    DetailView,
):
    permission_required = "staff_briefcase.view_staffbriefcase"
    template_name = "staff_briefcase/details.html"
    model = StaffBriefcase

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        briefcase = self.get_object()
        context["title"] = _(f"Briefcase - {briefcase.user.fullname}")
        context.setdefault(
            "briefcase_note_form",
            BriefcaseNoteMiniForm(initial={"briefcase": briefcase.pk}),
        )
        context.setdefault(
            "briefcase_document_form",
            BriefcaseDocumentMiniForm(initial={"briefcase": briefcase.pk}),
        )
        context.setdefault(
            "briefcase_account_form",
            BriefcaseAccountMiniForm(initial={"briefcase": briefcase.pk}),
        )
        return context


class StaffBriefcaseCreateView(
    PermissionRequiredMixin,
    BWManagerAssistantAccessMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    CreateView,
):
    permission_required = "staff_briefcase.add_staffbriefcase"
    template_name = "core/crudl/create.html"
    model = StaffBriefcase
    success_url = reverse_lazy("dashboard:briefcase:list")
