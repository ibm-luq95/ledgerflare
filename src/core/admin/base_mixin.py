"""Base admin mixin with audit, filtering, and soft delete capabilities."""
from __future__ import annotations

from typing import Any, ClassVar

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext as _
from import_export.admin import ImportExportModelAdmin
from rangefilter.filters import DateRangeFilterBuilder


class BWBaseAdminModelMixin(ImportExportModelAdmin, admin.ModelAdmin):
    """Mixin class for admin models in Beachwood Wood Financial."""

    import_error_display: tuple[str, str, str] = ("message", "row", "traceback")
    list_filter: ClassVar[list[tuple[str, Any]]] = [
        ("created_at", DateRangeFilterBuilder(title=_("Created at"))),
        ("updated_at", DateRangeFilterBuilder(title=_("Updated at"))),
    ]
    exclude: tuple[str, str, str] = ("metadata", "is_deleted", "deleted_at")
    actions: ClassVar[list[str]] = ["soft_delete_selected"]

    @admin.action(description=_("Soft delete selected items"))
    def soft_delete_selected(
        self, request: HttpRequest, queryset: QuerySet
    ) -> None:
        """Perform model-level soft delete on selected queryset items."""
        for obj in queryset:
            if hasattr(obj, "delete"):
                obj.delete()

    def get_actions(self, request: HttpRequest) -> dict[str, Any]:
        """Disable default hard-delete action in favor of soft-delete."""
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def has_delete_permission(
        self, request: HttpRequest, obj: Any | None = None
    ) -> bool:
        """Allow deletion only for superusers."""
        return bool(request.user and request.user.is_superuser)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Return the queryset for the admin model."""
        return self.model.original_objects.get_queryset()
