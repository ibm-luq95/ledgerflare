"""Client views module providing listing, creation, modification, deletion, export, and quick-peek features."""

from __future__ import annotations

import csv

from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from bookkeeper.models import BookkeeperProxy
from cfo.models.proxy import CFOProxy
from client.filters import ClientFilter
from client.forms import AssignBookkeeperForm, ClientForm, ClientMiniForm
from client.forms.assign_cfo import AssignCFOForm
from client.models import ClientProxy
from client_account.forms import ClientAccountForm
from client_category.forms import ClientCategoryForm
from client_category.models import ClientCategory
from core.cache import BWSiteSettingsViewMixin
from core.choices import ClientStatusEnum
from core.config.forms import BWFormRenderer
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.constants.identity import LedgerFlareIdentity
from core.constants.status_labels import CON_ARCHIVED, CON_ENABLED, CON_PAST_DUE
from core.constants.users import CON_ASSISTANT, CON_BOOKKEEPER, CON_CFO, CON_MANAGER
from core.utils.developments.enhanced_debugging_print import (
    ENHANCED_DEBUGGING_PRINT_INSTANCE,
    EnhancedDebuggingPrint,
)
from core.views.mixins import (
    BWBaseListViewMixin,
    BWLoginRequiredMixin,
    BWObjectAccessRequiredMixin,
)
from core.views.mixins.base_list_view import BWSectionDescriptionHelperMixin
from document.forms import DocumentForm

# from documents.forms import DocumentForm
from important_contact.forms import ImportantContactForm
from job.forms import JobMiniForm
from note.forms import NoteForm
from special_assignment.forms import MiniSpecialAssignmentForm
from task.forms import TaskForm


class ClientListView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    ListView,
):
    """List view for clients with KPI ribbon, filter accordion, and multi-mode layout."""

    permission_required = "client.can_view_list"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "client/list.html"
    model = ClientProxy
    paginate_by = LIST_VIEW_PAGINATE_BY
    list_type = "list"
    page_title = _("Clients")
    page_header = _("client".title())
    component_path = "bw_components/client/table_list.html"
    actions_base_url = "dashboard:client"
    filter_cancel_url = "dashboard:client:list"
    table_header_subtitle = _(
        "Comprehensive directory of active, onboarding, and managed client organizations."
    )
    pagination_list_url_name = "dashboard:client:list"
    actions_items = "details,update,delete"
    is_show_create_btn = True
    is_filters_enabled = True
    is_actions_menu_enabled = True
    is_header_enabled = True
    is_footer_enabled = True
    show_info_icon = False
    base_url_name = "dashboard:client"
    empty_label = _("client")
    subtitle = _(
        "Manage client accounts, business profiles, service tiers, and assigned financial teams."
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("extra_context", {"is_show_bookkeeper": True})

        base_qs = super().get_queryset()
        if self.request.user.user_type == CON_BOOKKEEPER:
            base_qs = self.request.user.bookkeeper.get_proxy_model().clients.all()
        elif self.request.user.user_type == CON_CFO:
            base_qs = self.request.user.cfo.get_proxy_model().clients.all()

        kpi_stats = base_qs.aggregate(
            total_clients=Count("id", distinct=True),
            active_clients=Count(
                "id", filter=Q(status=ClientStatusEnum.ENABLED), distinct=True
            ),
            unassigned_clients=Count(
                "id", filter=Q(bookkeepers__isnull=True), distinct=True
            ),
            total_active_jobs=Count(
                "jobs", filter=~Q(jobs__status=CON_ARCHIVED), distinct=True
            ),
        )
        context["kpi_stats"] = kpi_stats

        context.setdefault(
            "info_details",
            {
                "tooltip_txt": BW_INFO_MODAL_CSS_CLASSES.get("client").get(
                    "tooltip_txt"
                ),
                "modal_css_id": BW_INFO_MODAL_CSS_CLASSES.get("client").get("cssID"),
            },
        )
        context.setdefault("filter_categories_is_enabled", True)
        context.setdefault("filter_form_id", "clientFilterForm")
        if self.request.GET:
            context["title"] = _("Filtered Clients")
        else:
            context["title"] = _("Clients")
        context.setdefault(
            "filter_categories",
            {
                "categories_add_form": ClientCategoryForm,
                "categories_add_form_css_id": "clientCategoriesCreateForm",
                "categories_object_list": ClientCategory.objects.annotate(
                    clients_count=Count(
                        "clients",
                        filter=Q(clients__is_deleted=False),
                        distinct=True,
                    )
                ),
                "categories_add_form_css_class": "filterCategoryForms",
                "categories_modal_title": _("Client categories"),
                "category_app_label": "client_category",
                "category_filter_form_action_url": reverse_lazy(
                    "dashboard:client_category:api:client-category-api-router-list"
                ),
                "is_actions_menu_enabled": False,
            },
        )
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.user_type == CON_BOOKKEEPER:
            queryset = self.request.user.bookkeeper.get_proxy_model().clients.all()
        if self.request.user.user_type == CON_CFO:
            queryset = self.request.user.cfo.get_proxy_model().clients.all()

        queryset = queryset.annotate(
            total_jobs_count=Count("jobs", distinct=True),
            total_tasks_count=Count("jobs__tasks", distinct=True),
            total_special_assignments_count=Count("special_assignments", distinct=True),
            past_due_jobs_count=Count(
                "jobs", filter=Q(jobs__status=CON_PAST_DUE), distinct=True
            ),
        ).prefetch_related(
            "categories",
            Prefetch(
                "bookkeepers",
                queryset=BookkeeperProxy.objects.select_related("user"),
            ),
            Prefetch(
                "cfos",
                queryset=CFOProxy.objects.select_related("user"),
            ),
        )

        self.filterset = ClientFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs


class BaseClientExportView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    View,
):
    """Base class for exporting filtered clients."""

    permission_required = "client.can_view_list"
    permission_denied_message = _("You do not have permission to export clients.")

    def get_queryset(self):
        queryset = ClientProxy.objects.all()
        if self.request.user.user_type == CON_BOOKKEEPER:
            queryset = self.request.user.bookkeeper.get_proxy_model().clients.all()
        elif self.request.user.user_type == CON_CFO:
            queryset = self.request.user.cfo.get_proxy_model().clients.all()

        queryset = queryset.annotate(
            total_jobs_count=Count("jobs", distinct=True),
            past_due_jobs_count=Count(
                "jobs", filter=Q(jobs__status=CON_PAST_DUE), distinct=True
            ),
        ).prefetch_related(
            "bookkeepers",
            "cfos",
        )

        filterset = ClientFilter(self.request.GET, queryset=queryset)
        return filterset.qs


class ClientExportCsvView(BaseClientExportView):
    """Export filtered clients to CSV."""

    def get(self, request, *args, **kwargs):
        clients = self.get_queryset()
        from client.services import ClientExportService

        service = ClientExportService()
        return service.export_csv(clients)


class ClientExportExcelView(BaseClientExportView):
    """Export filtered clients to Excel (.xlsx)."""

    def get(self, request, *args, **kwargs):
        clients = self.get_queryset()
        from client.services import ClientExportService

        service = ClientExportService()
        return service.export_xlsx(clients)


class ClientExportView(BaseClientExportView):
    """Unified view to export clients in CSV or Excel format."""

    def get(self, request, *args, **kwargs):
        clients = self.get_queryset()
        export_format = request.GET.get("format", "csv").lower()
        from client.services import ClientExportService

        service = ClientExportService()
        if export_format in ["xlsx", "excel"]:
            return service.export_xlsx(clients)
        return service.export_csv(clients)


class ClientQuickPeekView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    DetailView,
):
    """Render lightweight partial HTML for Quick Peek Slide-Over Drawer."""

    permission_required = "client.can_view_list"
    model = ClientProxy
    template_name = "bw_components/client/quick_peek_content.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                total_jobs_count=Count("jobs", distinct=True),
                total_tasks_count=Count("jobs__tasks", distinct=True),
                past_due_jobs_count=Count(
                    "jobs", filter=Q(jobs__status=CON_PAST_DUE), distinct=True
                ),
            )
            .prefetch_related(
                "categories",
                "important_contacts",
                Prefetch(
                    "bookkeepers",
                    queryset=BookkeeperProxy.objects.select_related("user"),
                ),
                Prefetch(
                    "cfos",
                    queryset=CFOProxy.objects.select_related("user"),
                ),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client_obj = self.object
        context["active_jobs"] = client_obj.jobs.filter(~Q(status=CON_ARCHIVED))[:5]
        context["recent_notes"] = client_obj.notes.all()[:3]
        return context


class ClientCreateView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    CreateView,
):
    # permission_required = ("client.add_client", "client.add_client")
    permission_required = "client.add_client"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "client/create.html"
    form_class = ClientForm
    success_message = _("Client created successfully")
    success_url = reverse_lazy("dashboard:client:list")

    # template_name_suffix = "_create_client"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Create client"))
        return context


# def form_valid(self, form: BaseForm):
#     debugging_print(form.cleaned_data)
#     return super().form_valid(form)


class ClientUpdateView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    UpdateView,
):
    permission_required = "client.change_client"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "client/update.html"
    form_class = ClientForm
    success_message = _("Client updated successfully")
    success_url = reverse_lazy("dashboard:client:list")
    model = ClientProxy

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Update client"))
        return context


class ClientDeleteView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    DeleteView,
):
    template_name = "core/crudl/delete.html"
    permission_required = "client.delete_client"
    permission_denied_message = _("You do not have permission to access this page.")
    model = ClientProxy
    success_message = _("Client deleted successfully")
    success_url = reverse_lazy("dashboard:client:list")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Delete client"))
        context.setdefault("cancel_url", "dashboard:client:list")
        context.setdefault("object", self.get_object())
        context.setdefault("object_name", "client")
        context.setdefault("form_css_id", "clientDeleteForm")
        return context


class ClientDetailsView(
    PermissionRequiredMixin,
    UserPassesTestMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWSectionDescriptionHelperMixin,
    DetailView,
):
    template_name = "client/details.html"

    model = ClientProxy
    permission_required = "client.view_client"
    permission_denied_message = _("You do not have permission to access this page.")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _(f"Client - {self.get_object().name}"))
        job_form = JobMiniForm(
            initial={"client": self.get_object().pk},
            client=self.get_object(),
        )
        important_contact_form = ImportantContactForm(
            initial={"client": self.get_object()},
            renderer=BWFormRenderer(),
        )
        client_form = ClientForm(
            instance=self.get_object(),
            renderer=BWFormRenderer(),
            removed_fields=[
                "categories",
                "bookkeepers",
                "important_contacts",
                "status",
            ],
        )
        client_mini_form = ClientMiniForm()
        task_form = TaskForm(
            initial={"client": self.get_object()},
            # removed_fields=["job"],
            hidden_fields=["job"],
            renderer=BWFormRenderer(),
        )
        document_form = DocumentForm(
            initial={"client": self.get_object(), "document_section": "client"},
            renderer=BWFormRenderer(),
            removed_fields=["task", "status", "job"],
            hidden_inputs={"field_names": ["client"]},
        )
        note_form = NoteForm(
            renderer=BWFormRenderer(),
            initial={"client": self.get_object()},
            removed_fields=["task", "job"],
            hidden_inputs={"field_names": ["client"]},
        )
        special_assignment_form = MiniSpecialAssignmentForm(
            renderer=BWFormRenderer(),
            initial={
                "assigned_by": self.request.user.pk,
                "client": self.get_object().pk,
            },
        )
        client_account_form = ClientAccountForm(
            initial={"client": self.get_object(), "status": CON_ENABLED},
            renderer=BWFormRenderer(),
            hidden_inputs={"field_names": ["client", "status"]},
        )
        client_assign_bookkeeper_form = AssignBookkeeperForm(
            renderer=BWFormRenderer(), client=self.get_object()
        )
        client_assign_cfo_form = AssignCFOForm(
            renderer=BWFormRenderer(), client=self.get_object()
        )
        context.setdefault("job_form", job_form)
        # context.setdefault("job_status_choices", JobStatusEnum.choices)
        context.setdefault("task_form", task_form)
        context.setdefault("document_form", document_form)
        context.setdefault("client_form", client_form)
        context.setdefault("important_contact_form", important_contact_form)
        context.setdefault("note_form", note_form)
        context.setdefault("client_mini_form", client_mini_form)
        context.setdefault("special_assignment_form", special_assignment_form)
        context.setdefault("client_account_form", client_account_form)
        context.setdefault(
            "client_assign_bookkeeper_form", client_assign_bookkeeper_form
        )
        context.setdefault("client_assign_cfo_form", client_assign_cfo_form)
        return context

    def test_func(self) -> bool:
        """Check if current user is authorized to view client details."""
        user_type = self.request.user.user_type
        if user_type in {CON_MANAGER, CON_ASSISTANT}:
            return True
        if user_type == CON_BOOKKEEPER and hasattr(self.request.user, "bookkeeper"):
            bookkeeper = self.request.user.bookkeeper
            return self.get_object().bookkeepers.filter(pk=bookkeeper.pk).exists()
        if user_type == CON_CFO and hasattr(self.request.user, "cfo"):
            cfo = self.request.user.cfo
            return self.get_object().cfos.filter(pk=cfo.pk).exists()
        return False
