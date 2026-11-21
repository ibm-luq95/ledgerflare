# -*- coding: utf-8 -*-#
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import CreateView, UpdateView, ListView, DeleteView

from client_category.filters import ClientCategoryFilter
from client_category.forms import ClientCategoryForm
from client_category.models import ClientCategory
from core.cache import BWSiteSettingsViewMixin
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.utils import get_trans_txt
from core.views.mixins import BWBaseListViewMixin, BWLoginRequiredMixin


class ClientCategoryListViewBW(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    ListView,
):
    template_name = "core/crudl/list.html"
    model = ClientCategory
    permission_required = "client_category.can_view_list"
    permission_denied_message = _("You do not have permission to access this page.")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", get_trans_txt("Client Categories"))
        context.setdefault("filter_form", self.filterset.form)
        context.setdefault("page_header", _("clients categories".capitalize()))
        context.setdefault(
            "component_path", "bw_components/client_category/table_list.html"
        )
        context.setdefault(
            "subtitle",
            _(
                "Categorize client accounts by industry, service tier, and corporate classification."
            ),
        )
        context.setdefault("actions_base_url", "dashboard:client_category")
        context.setdefault("filter_cancel_url", "dashboard:client_category:list")
        context.setdefault("table_header_title", _("C"))
        context.setdefault(
            "table_header_subtitle",
            _("Industry groups, service tiers, and classification taxonomy."),
        )
        context.setdefault("is_show_create_btn", True)
        context.setdefault("pagination_list_url_name", "dashboard:client_category:list")
        context.setdefault("is_filters_enabled", True)
        context.setdefault("is_actions_menu_enabled", True)
        context.setdefault("is_header_enabled", True)
        context.setdefault("is_footer_enabled", True)
        context.setdefault("actions_items", "update,delete")
        context.setdefault("base_url_name", "dashboard:client_category")
        context.setdefault("empty_label", _("categories"))
        context.setdefault("extra_context", {})
        context.setdefault("show_info_icon", True)
        context.setdefault(
            "info_details",
            {
                "tooltip_txt": BW_INFO_MODAL_CSS_CLASSES.get("client_category").get(
                    "tooltip_txt"
                ),
                "modal_css_id": BW_INFO_MODAL_CSS_CLASSES.get("client_category").get(
                    "cssID"
                ),
            },
        )
        context.setdefault("filter_form_id", "clientCategoryFilterForm")
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = ClientCategoryFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs


class ClientCategoryCreateView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    CreateView,
):
    template_name = "client_category/create.html"
    form_class = ClientCategoryForm
    model = ClientCategory
    success_message = _("Category created successfully")
    success_url = reverse_lazy("dashboard:client_category:list")
    permission_required = "client_category.add_clientcategory"
    permission_denied_message = _("You do not have permission to access this page.")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", get_trans_txt("Create client category"))
        messages.set_level(self.request, messages.DEBUG)
        return context


class ClientCategoryUpdateView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    UpdateView,
):
    template_name = "client_category/update.html"
    form_class = ClientCategoryForm
    model = ClientCategory
    success_message = _("Category updated successfully")
    success_url = reverse_lazy("dashboard:client_category:list")
    permission_required = "client_category.change_clientcategory"
    permission_denied_message = _("You do not have permission to access this page.")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", get_trans_txt("Update client category"))
        messages.set_level(self.request, messages.DEBUG)
        return context


class ClientCategoryDeleteView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    DeleteView,
):
    permission_required = "client_category.delete_clientcategory"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "core/crudl/delete.html"
    model = ClientCategory
    success_message = _("Category deleted successfully")
    success_url = reverse_lazy("dashboard:client_category:list")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", get_trans_txt("Delete client category"))
        context.setdefault("cancel_url", "dashboard:client_category:list")
        context.setdefault("object", self.get_object())
        context.setdefault("object_name", "client category")
        context.setdefault("form_css_id", "clientCategoryDeleteForm")
        return context
