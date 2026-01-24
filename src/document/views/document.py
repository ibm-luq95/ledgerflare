# -*- coding: utf-8 -*-#
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.cache import BWSiteSettingsViewMixin
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.constants.users import CON_BOOKKEEPER
from core.views.mixins import BWBaseListViewMixin, BWLoginRequiredMixin
from core.views.mixins.bookkeeper_pass_related_mixin import BookkeeperPassRelatedMixin
from core.views.mixins.update_previous_mixin import UpdateReturnPreviousMixin
from document.filters import DocumentFilter
from document.forms import DocumentForm
from document.models import Document


class DocumentListView(
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
    list_type = "list"
    is_show_create_btn = True
    is_filters_enabled = True
    is_actions_menu_enabled = True
    is_header_enabled = True
    is_footer_enabled = True
    show_info_icon = False
    page_title = _("Documents")
    page_header = _("Documents".title())
    component_path = "bw_components/document/table_list.html"
    actions_base_url = "dashboard:document"
    filter_cancel_url = "dashboard:document:list"
    subtitle = _("documents".title())
    pagination_list_url_name = "dashboard:document:list"
    base_url_name = "dashboard:document"
    empty_label = _("documents")
    actions_items = "update,delete"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # context.setdefault("filter_form", self.filterset.form)
        context.setdefault("table_header_subtitle", _("documents subtitle"))
        context.setdefault(
            "extra_context",
            {
                "is_show_section": True,
                "is_show_job_link": True,
                "is_show_client_link": True,
                "is_show_task_link": True,
            },
        )
        context.setdefault("show_info_icon", True)
        context.setdefault(
            "info_details",
            {
                "tooltip_txt": BW_INFO_MODAL_CSS_CLASSES.get("document").get(
                    "tooltip_txt"
                ),
                "modal_css_id": BW_INFO_MODAL_CSS_CLASSES.get("document").get("cssID"),
            },
        )
        context.setdefault("filter_form_id", "documentFilterForm")

        # debugging_print(self.filterset.form["name"])
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.user_type == CON_BOOKKEEPER:
            queryset = (
                self.request.user.bookkeeper.get_proxy_model().get_all_related_items(
                    "documents"
                )
            )
        self.filterset = DocumentFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs


class DocumentCreateView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    BookkeeperPassRelatedMixin,
    CreateView,
):
    permission_required = "document.add_document"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "document/create.html"
    form_class = DocumentForm
    success_message = _("Document created successfully")
    success_url = reverse_lazy("dashboard:document:list")

    # template_name_suffix = "_create_client"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Create document"))
        return context

    # def form_valid(self, form: BaseForm):
    #     debugging_print(form.cleaned_data)
    #     return super().form_valid(form)
    #
    # def form_invalid(self, form):
    #     """If the form is invalid, render the invalid form."""
    #     debugging_print(form.cleaned_data)
    #     return self.render_to_response(self.get_context_data(form=form))


class DocumentUpdateView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    BookkeeperPassRelatedMixin,
    UpdateReturnPreviousMixin,
    UpdateView,
):
    permission_required = "document.change_document"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "document/update.html"
    form_class = DocumentForm
    success_message = _("Document updated successfully")
    # success_url = reverse_lazy("dashboard:document:list")
    model = Document
    BASE_SUCCESS_URL = "dashboard:document:list"

    # template_name_suffix = "_create_client"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Update document"))
        return context

    def get_form_kwargs(self):
        """Return the keyword arguments for instantiating the form."""
        kwargs = super().get_form_kwargs()
        # sections = ["job", "client", "task"]
        object = self.get_object()
        # for sec in sections:
        #     if sec == object.document_section:
        #         sections.remove(sec)
        # kwargs.update({"is_update": True, "removed_fields": sections})
        kwargs.update({"is_update": True})
        return kwargs


class DocumentDeleteView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    DeleteView,
):
    permission_required = "document.delete_document"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "core/crudl/delete.html"
    model = Document
    success_message = _("Document deleted successfully")
    success_url = reverse_lazy("dashboard:document:list")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Delete document"))
        context.setdefault("cancel_url", "dashboard:document:list")
        context.setdefault("object", self.get_object())
        context.setdefault("object_name", "document")
        context.setdefault("form_css_id", "documentDeleteForm")
        return context
