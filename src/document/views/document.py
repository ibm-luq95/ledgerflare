from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, View

from core.cache import BWSiteSettingsViewMixin
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.constants.users import CON_BOOKKEEPER, CON_CFO
from core.views.mixins import (
    BWBaseListViewMixin,
    BWLoginRequiredMixin,
    BWObjectAccessRequiredMixin,
)
from core.views.mixins.bookkeeper_pass_related_mixin import BookkeeperPassRelatedMixin
from core.views.mixins.update_previous_mixin import UpdateReturnPreviousMixin
from document.filters import DocumentFilter
from document.forms import DocumentForm
from document.models import Document, DocumentProxy


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
    paginate_by = LIST_VIEW_PAGINATE_BY
    list_type = "list"
    is_show_create_btn = True
    is_filters_enabled = True
    is_actions_menu_enabled = True
    is_header_enabled = True
    is_footer_enabled = True
    show_info_icon = True
    page_title = _("Documents")
    page_header = _("Documents".title())
    component_path = "bw_components/document/table_list.html"
    actions_base_url = "dashboard:document"
    filter_cancel_url = "dashboard:document:list"
    table_header_title = _("C")
    pagination_list_url_name = "dashboard:document:list"
    actions_items = "update,delete"
    base_url_name = "dashboard:document"
    empty_label = _("documents")
    subtitle = _(
        "Secure repository for financial statements, tax filings, legal agreements, and client records."
    )

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
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
        context.setdefault("filter_form_id", "documentsFilterForm")
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.user_type == CON_BOOKKEEPER:
            queryset = (
                self.request.user.bookkeeper.get_proxy_model().get_all_related_items(
                    "documents"
                )
            )
        elif self.request.user.user_type == CON_CFO:
            queryset = self.request.user.cfo.get_proxy_model().get_all_related_items(
                "documents"
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

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Create document"))
        return context


class DocumentUpdateView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
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
    model = Document
    BASE_SUCCESS_URL = "dashboard:document:list"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Update document"))
        return context

    def get_form_kwargs(self):
        """Return the keyword arguments for instantiating the form."""
        kwargs = super().get_form_kwargs()
        kwargs.update({"is_update": True})
        return kwargs


class DocumentDeleteView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
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


class DocumentDownloadView(
    PermissionRequiredMixin,
    BWObjectAccessRequiredMixin,
    BWLoginRequiredMixin,
    View,
):
    """Download and transparently decrypt document files for users."""

    permission_required = "document.can_view_list"
    permission_denied_message = _(
        "You do not have permission to download this document."
    )
    object: DocumentProxy | None = None

    def get_object(self, queryset: Any = None) -> DocumentProxy:
        """Retrieve and cache the target DocumentProxy by primary key."""
        if self.object is not None:
            return self.object
        pk = self.kwargs.get("pk")
        self.object = get_object_or_404(DocumentProxy, pk=pk)
        return self.object

    def get(self, request: Any, *args: Any, **kwargs: Any) -> FileResponse:
        """Stream decrypted document content with correct MIME headers."""
        document = self.get_object()
        if not document.document_file:
            raise Http404(_("No file associated with this document"))

        try:
            file_obj = document.document_file.open("rb")
        except FileNotFoundError as err:
            raise Http404(_("Document file not found on disk")) from err

        raw_name = Path(str(document.document_file.name)).name
        clean_name = (
            raw_name.split("_", 1)[-1] if "_" in raw_name else raw_name
        )
        content_type, _encoding = mimetypes.guess_type(clean_name)

        return FileResponse(
            file_obj,
            as_attachment=True,
            filename=clean_name,
            content_type=content_type or "application/octet-stream",
        )

