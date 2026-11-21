from __future__ import annotations

from typing import Any
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _

from core.models.mixins import BaseModelMixin

class NotificationVerb(models.TextChoices):
    CREATED = "created", _("Created")
    UPDATED = "updated", _("Updated")
    DELETED = "deleted", _("Deleted")
    ASSIGNED = "assigned", _("Assigned")
    COMMENTED = "commented", _("Commented")
    STATUS_CHANGED = "status_changed", _("Status Changed")

class Notification(BaseModelMixin):
    actor = models.ForeignKey(
        to="beach_wood_user.BWUser",
        on_delete=models.SET_NULL,
        related_name="triggered_notifications",
        null=True,
        blank=True,
    )
    verb = models.CharField(
        max_length=20,
        choices=NotificationVerb.choices,
        default=NotificationVerb.CREATED,
    )
    message_template = models.TextField(
        _("message template"),
        help_text=_("Template string or final message text"),
    )
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    object_id = models.UUIDField(
        null=True,
        blank=True,
    )
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta(BaseModelMixin.Meta):
        ordering = ["-created_at"]
        verbose_name = _("notification")
        verbose_name_plural = _("notifications")
        db_table = "lf_notifications_notification"
        indexes = [
            models.Index(fields=["content_type", "object_id"], name="lf_notification_gfk_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.actor} - {self.verb}"

    def get_absolute_url(self) -> str:
        if self.content_object and hasattr(self.content_object, "get_absolute_url"):
            return self.content_object.get_absolute_url()
        return "#"

    def get_actor_role_display(self) -> str:
        if not self.actor:
            return "System"
        if hasattr(self.actor, "get_user_type_display") and self.actor.user_type:
            return str(self.actor.get_user_type_display())
        return "Staff"

    def get_entity_breadcrumb(self) -> dict[str, str] | None:
        """Returns entity context details (client name, target object title, type) if available."""
        obj = self.content_object
        if not obj:
            return None

        # Discussion / DiscussionProxy
        if hasattr(obj, "for_what"):
            target = obj.for_what()
            if target:
                obj = target

        # Model with client relation (Job, SpecialAssignment)
        if hasattr(obj, "client") and obj.client:
            client_name = str(getattr(obj.client, "name", obj.client))
            title = str(getattr(obj, "title", obj))
            target_type = obj._meta.verbose_name.title()
            return {
                "client_name": client_name,
                "target_title": title,
                "target_type": target_type,
            }

        # Client model directly
        if hasattr(obj, "name"):
            return {
                "client_name": str(obj.name),
                "target_title": "",
                "target_type": "Client",
            }

        return None

    def get_entity_status_badge(self) -> dict[str, str] | None:
        """Returns status badge details (label, styling) if target entity is archived or completed."""
        obj = self.content_object
        if not obj:
            return None

        # Discussion / DiscussionProxy target object
        if hasattr(obj, "for_what"):
            target = obj.for_what()
            if target:
                obj = target

        # Check soft-deleted or archived
        if getattr(obj, "is_deleted", False) or getattr(obj, "is_archived", False):
            return {
                "label": "Archived",
                "bg_css": "bg-gray-100 text-gray-600 dark:bg-neutral-800 dark:text-neutral-400 border border-gray-200/60 dark:border-neutral-700/60",
            }

        # Check status attribute (Job, SpecialAssignment, etc.)
        status = getattr(obj, "status", None)
        if status:
            status_str = str(status).lower()
            if status_str in ["completed", "done", "finished"]:
                return {
                    "label": "Completed",
                    "bg_css": "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300 border border-emerald-200/60 dark:border-emerald-800/60",
                }
            elif status_str in ["past_due", "overdue"]:
                return {
                    "label": "Overdue",
                    "bg_css": "bg-rose-100 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300 border border-rose-200/60 dark:border-rose-800/60",
                }
            elif status_str in ["in_progress", "in-progress"]:
                return {
                    "label": "In Progress",
                    "bg_css": "bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300 border border-amber-200/60 dark:border-amber-800/60",
                }

        return None

class NotificationProxy(Notification):
    class Meta(Notification.Meta):
        proxy = True
        indexes = []
