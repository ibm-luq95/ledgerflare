from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from client_account.filters import ClientAccountFilter
from client_account.forms import ClientAccountForm
from client_account.models import ClientAccount
from core.cache import BWSiteSettingsViewMixin
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.constants.users import (
    CON_ASSISTANT,
    CON_BOOKKEEPER,
    CON_CFO,
    CON_MANAGER,
)
from core.utils import get_trans_txt
from core.views.mixins import (
    BWBaseListViewMixin,
    BWLoginRequiredMixin,
    BWObjectAccessRequiredMixin,
)
from core.views.mixins.update_previous_mixin import UpdateReturnPreviousMixin


class ClientAccountListViewBW(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    ListView,
):
    template_name = "core/crudl/list.html"
    model = ClientAccount
    permission_required = "client_account.can_view_list"
    permission_denied_message = _("You do not have permission to access this page.")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.setdefault("title", get_trans_txt("Client Accounts"))
        context.setdefault("filter_form", self.filterset.form)
        context.setdefault("page_header", _("client accounts".capitalize()))
        context.setdefault(
            "component_path", "bw_components/client_account/table_list.html"
        )
        context.setdefault(
            "subtitle",
            _(
                "Encrypted credentials, portal logins, and banking access configurations for client accounts."
            ),
        )
        context.setdefault("actions_base_url", "dashboard:client_account")
        context.setdefault("filter_cancel_url", "dashboard:client_account:list")
        context.setdefault("table_header_title", _("C"))
        context.setdefault(
            "table_header_subtitle",
            _(
                "Secure credential vault, external portal logins, and authorized credentials."
            ),
        )
        context.setdefault("is_show_create_btn", True)
        context.setdefault("pagination_list_url_name", "dashboard:client_account:list")
        context.setdefault("is_filters_enabled", True)
        context.setdefault("is_actions_menu_enabled", True)
        context.setdefault("is_header_enabled", True)
        context.setdefault("is_footer_enabled", True)
        context.setdefault("actions_items", "update,delete")
        context.setdefault("base_url_name", "dashboard:client_account")
        context.setdefault("empty_label", _("accounts"))
        context.setdefault("extra_context", {})
        context.setdefault("show_info_icon", True)
        context.setdefault(
            "info_details",
            {
                "tooltip_txt": BW_INFO_MODAL_CSS_CLASSES.get("client_account").get(
                    "tooltip_txt"
                ),
                "modal_css_id": BW_INFO_MODAL_CSS_CLASSES.get("client_account").get(
                    "cssID"
                ),
            },
        )
        context.setdefault("filter_form_id", "clientAccountFilterForm")
        return context

    def get_queryset(self) -> QuerySet[ClientAccount]:
        queryset = super().get_queryset()
        user = self.request.user
        if user.user_type == CON_BOOKKEEPER:
            clients = user.bookkeeper.get_proxy_model().clients.all()
            qs = ClientAccount.objects.filter(client__in=clients)
        elif user.user_type == CON_CFO:
            clients = user.cfo.get_proxy_model().clients.all()
            qs = ClientAccount.objects.filter(client__in=clients)
        elif user.user_type in (CON_MANAGER, CON_ASSISTANT) or user.is_superuser:
            qs = queryset
        else:
            qs = ClientAccount.objects.none()
        self.filterset = ClientAccountFilter(self.request.GET, queryset=qs)
        return self.filterset.qs


class ClientAccountCreateView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    CreateView,
):
    template_name = "client_account/create.html"
    form_class = ClientAccountForm
    model = ClientAccount
    success_message = _("Client account created successfully")
    success_url = reverse_lazy("dashboard:client_account:list")
    permission_required = "client_account.add_clientaccount"
    permission_denied_message = _("You do not have permission to access this page.")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.setdefault("title", get_trans_txt("Create account"))
        messages.set_level(self.request, messages.DEBUG)
        return context


class ClientAccountUpdateView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    UpdateReturnPreviousMixin,
    UpdateView,
):
    template_name = "client_account/update.html"
    form_class = ClientAccountForm
    model = ClientAccount
    success_message = _("Contact updated successfully")
    permission_required = "client_account.change_clientaccount"
    permission_denied_message = _("You do not have permission to access this page.")
    BASE_SUCCESS_URL = "dashboard:client_account:list"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.setdefault("title", get_trans_txt("Update account"))
        messages.set_level(self.request, messages.DEBUG)
        return context

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs.update({"is_update": True, "updated_object": self.get_object()})
        return kwargs


class ClientAccountDeleteView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    DeleteView,
):
    template_name = "core/crudl/delete.html"
    model = ClientAccount
    success_message = _("Contact deleted successfully")
    success_url = reverse_lazy("dashboard:client_account:list")
    permission_required = "client_account.delete_clientaccount"
    permission_denied_message = _("You do not have permission to access this page.")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.setdefault("title", get_trans_txt("Delete account"))
        context.setdefault("cancel_url", "dashboard:client_account:list")
        context.setdefault("object", self.get_object())
        context.setdefault("object_name", "client account")
        context.setdefault("form_css_id", "clientAccountDeleteForm")
        return context
