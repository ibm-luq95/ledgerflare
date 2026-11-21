from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Prefetch, Q, QuerySet
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

from client.models import ClientProxy
from core.cache import BWSiteSettingsViewMixin
from core.choices import ImportantContactLabelsEnum
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.constants.identity import LedgerFlareIdentity
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
from important_contact.filters import ImportantContactFilter
from important_contact.forms import ImportantContactForm
from important_contact.models import ImportantContactProxy


class ImportantContactListViewBW(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    ListView,
):
    """Refactored Important Contact list view with KPI stats and query optimization."""

    template_name = "important_contact/list.html"
    model = ImportantContactProxy
    paginate_by = LIST_VIEW_PAGINATE_BY
    permission_required = "important_contact.can_view_list"
    permission_denied_message = _("You do not have permission to access this page.")
    list_type = "list"
    page_title = _("Important Contacts")
    page_header = _("Important Contacts")
    component_path = "bw_components/important_contact/table_list.html"
    actions_base_url = "dashboard:important_contact"
    filter_cancel_url = "dashboard:important_contact:list"
    is_show_create_btn = True
    is_filters_enabled = True
    is_actions_menu_enabled = True
    is_header_enabled = True
    is_footer_enabled = True
    show_info_icon = True
    pagination_list_url_name = "dashboard:important_contact:list"
    base_url_name = "dashboard:important_contact"
    empty_label = _("contact")
    actions_items = "update,delete"
    subtitle = _(
        "Key executive contacts, payroll authorities, and corporate stakeholders across client accounts."
    )

    def get_scoped_base_queryset(self) -> QuerySet[ImportantContactProxy]:
        """Return role-scoped queryset before filter application."""
        current_user = self.request.user
        if not current_user.is_authenticated:
            return ImportantContactProxy.objects.none()

        if (
            current_user.user_type in (CON_MANAGER, CON_ASSISTANT)
            or current_user.is_superuser
        ):
            return ImportantContactProxy.objects.all()
        if current_user.user_type == CON_BOOKKEEPER and hasattr(
            current_user, "bookkeeper"
        ):
            bookkeeper_clients = current_user.bookkeeper.get_proxy_model().clients.all()
            if bookkeeper_clients:
                return ImportantContactProxy.objects.filter(
                    client__in=bookkeeper_clients
                ).distinct()
            return ImportantContactProxy.objects.none()
        if current_user.user_type == CON_CFO and hasattr(current_user, "cfo"):
            cfo_clients = current_user.cfo.get_proxy_model().clients.all()
            if cfo_clients:
                return ImportantContactProxy.objects.filter(
                    client__in=cfo_clients
                ).distinct()
            return ImportantContactProxy.objects.none()
        return ImportantContactProxy.objects.none()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Inject aggregate KPI metrics, filter forms, and UI configuration context."""
        context = super().get_context_data(**kwargs)
        base_qs = self.get_scoped_base_queryset()

        kpi_stats = base_qs.aggregate(
            total_contacts=Count("id", distinct=True),
            payroll_contacts=Count(
                "id",
                filter=Q(contact_label=ImportantContactLabelsEnum.PAYROLL),
                distinct=True,
            ),
            ceo_contacts=Count(
                "id",
                filter=Q(contact_label=ImportantContactLabelsEnum.CEO),
                distinct=True,
            ),
            other_contacts=Count(
                "id",
                filter=Q(contact_label=ImportantContactLabelsEnum.OTHER),
                distinct=True,
            ),
            linked_clients_contacts=Count(
                "id",
                filter=Q(client__isnull=False),
                distinct=True,
            ),
        )
        context["kpi_stats"] = kpi_stats
        context["total_records"] = kpi_stats.get("total_contacts", 0)

        filter_form = getattr(self, "filterset", None) and self.filterset.form
        if filter_form is None:
            filter_form = ImportantContactFilter(
                self.request.GET, queryset=base_qs
            ).form
        context["filter_form"] = filter_form
        context.setdefault("filter_form_id", "importantContactFilterForm")
        context.setdefault(
            "info_details",
            {
                "tooltip_txt": BW_INFO_MODAL_CSS_CLASSES.get(
                    "important_contact", {}
                ).get("tooltip_txt", ""),
                "modal_css_id": BW_INFO_MODAL_CSS_CLASSES.get(
                    "important_contact", {}
                ).get("cssID", ""),
            },
        )
        if self.request.GET:
            context["title"] = _("Filtered Important Contacts")
        else:
            context["title"] = _("Important Contacts")
        return context

    def get_queryset(self) -> QuerySet[ImportantContactProxy]:
        """Return eager-loaded filtered contacts queryset avoiding N+1 queries."""
        queryset = self.get_scoped_base_queryset()
        queryset = queryset.prefetch_related(
            Prefetch("client", queryset=ClientProxy.objects.all())
        )
        self.filterset = ImportantContactFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs


class ImportantContactQuickPeekView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    DetailView,
):
    """Render partial HTML for Quick Peek Slide-Over Drawer."""

    permission_required = "important_contact.can_view_list"
    model = ImportantContactProxy
    template_name = "bw_components/important_contact/quick_peek_content.html"

    def get_queryset(self) -> QuerySet[ImportantContactProxy]:
        return (
            super()
            .get_queryset()
            .prefetch_related(Prefetch("client", queryset=ClientProxy.objects.all()))
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["today"] = timezone.now().date()
        return context


class BaseImportantContactExportView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    View,
):
    """Base class for exporting filtered important contacts."""

    permission_required = "important_contact.can_view_list"
    permission_denied_message = _("You do not have permission to export contacts.")

    def get_queryset(self) -> QuerySet[ImportantContactProxy]:
        view_instance = ImportantContactListViewBW()
        view_instance.request = self.request
        base_qs = view_instance.get_scoped_base_queryset()
        base_qs = base_qs.prefetch_related(
            Prefetch("client", queryset=ClientProxy.objects.all())
        )
        filterset = ImportantContactFilter(self.request.GET, queryset=base_qs)
        return filterset.qs


class ImportantContactExportCsvView(BaseImportantContactExportView):
    """View to export contacts to CSV format."""

    def get(self, request: Any, *args: Any, **kwargs: Any) -> HttpResponse:
        contacts = self.get_queryset()
        from important_contact.services import ImportantContactExportService

        service = ImportantContactExportService()
        return service.export_csv(contacts)


class ImportantContactExportExcelView(BaseImportantContactExportView):
    """View to export contacts to XLSX format."""

    def get(self, request: Any, *args: Any, **kwargs: Any) -> HttpResponse:
        contacts = self.get_queryset()
        from important_contact.services import ImportantContactExportService

        service = ImportantContactExportService()
        return service.export_xlsx(contacts)


class ImportantContactExportView(BaseImportantContactExportView):
    """Unified view to export contacts based on format param ('csv' or 'xlsx')."""

    def get(self, request: Any, *args: Any, **kwargs: Any) -> HttpResponse:
        contacts = self.get_queryset()
        export_format = request.GET.get("format", "csv").lower()
        from important_contact.services import ImportantContactExportService

        service = ImportantContactExportService()
        if export_format in ["xlsx", "excel"]:
            return service.export_xlsx(contacts)
        return service.export_csv(contacts)


class ImportantContactCreateView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    SuccessMessageMixin,
    CreateView,
):
    permission_required = "important_contact.add_importantcontact"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "important_contact/create.html"
    form_class = ImportantContactForm
    model = ImportantContactProxy
    success_message = _("Contact created successfully")
    success_url = reverse_lazy("dashboard:important_contact:list")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.setdefault("title", get_trans_txt("Create contact"))
        messages.set_level(self.request, messages.DEBUG)
        return context


class ImportantContactUpdateView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    UpdateReturnPreviousMixin,
    UpdateView,
):
    template_name = "important_contact/update.html"
    permission_required = "important_contact.change_importantcontact"
    permission_denied_message = _("You do not have permission to access this page.")
    form_class = ImportantContactForm
    model = ImportantContactProxy
    success_message = _("Contact updated successfully")
    BASE_SUCCESS_URL = "dashboard:important_contact:list"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.setdefault("title", get_trans_txt("Update contact"))
        messages.set_level(self.request, messages.DEBUG)
        return context


class ImportantContactDeleteView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    DeleteView,
):
    template_name = "core/crudl/delete.html"
    permission_required = "important_contact.delete_importantcontact"
    permission_denied_message = _("You do not have permission to access this page.")
    model = ImportantContactProxy
    success_message = _("Contact deleted successfully")
    success_url = reverse_lazy("dashboard:important_contact:list")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.setdefault("title", get_trans_txt("Delete contact"))
        context.setdefault("cancel_url", "dashboard:important_contact:list")
        context.setdefault("object", self.get_object())
        context.setdefault("object_name", "client contact")
        context.setdefault("form_css_id", "importantContactDeleteForm")
        return context
