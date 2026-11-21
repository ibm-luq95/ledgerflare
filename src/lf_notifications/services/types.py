from __future__ import annotations

from typing import Any, Dict
from django.utils.translation import gettext_lazy as _
from lf_notifications.services.registry import BaseNotificationType, register_notification_type

@register_notification_type
class DiscussionCreatedNotification(BaseNotificationType):
    name = "discussion_created"
    verbose_name = _("New Discussion")
    default_channels = ["in_app", "email"]

    @classmethod
    def get_message(cls, context: Dict[str, Any]) -> str:
        actor = context.get("actor_name", _("Someone"))
        target = context.get("target_name", _("a discussion"))
        return _(f"{actor} started a new discussion in {target}")

    @classmethod
    def get_action_url(cls, context: Dict[str, Any]) -> str:
        return context.get("url", "/")

@register_notification_type
class SpecialAssignmentAssignedNotification(BaseNotificationType):
    name = "assignment_assigned"
    verbose_name = _("Special Assignment Assigned")
    default_channels = ["in_app", "email"]

    @classmethod
    def get_message(cls, context: Dict[str, Any]) -> str:
        actor = context.get("actor_name", _("Someone"))
        title = context.get("assignment_title", _("an assignment"))
        return _(f"{actor} assigned you a new special assignment: {title}")

    @classmethod
    def get_action_url(cls, context: Dict[str, Any]) -> str:
        return context.get("url", "/")

@register_notification_type
class JobScheduledNotification(BaseNotificationType):
    name = "job_scheduled"
    verbose_name = _("Job Scheduled")
    default_channels = ["in_app"]

    @classmethod
    def get_message(cls, context: Dict[str, Any]) -> str:
        title = context.get("job_title", _("a job"))
        return _(f"Job scheduled: {title}")

    @classmethod
    def get_action_url(cls, context: Dict[str, Any]) -> str:
        return context.get("url", "/")

@register_notification_type
class JobPastDueNotification(BaseNotificationType):
    name = "job_past_due"
    verbose_name = _("Job Past Due")
    default_channels = ["in_app", "email"]

    @classmethod
    def get_message(cls, context: Dict[str, Any]) -> str:
        title = context.get("job_title", _("a job"))
        return _(f"Job is past due: {title}")

    @classmethod
    def get_action_url(cls, context: Dict[str, Any]) -> str:
        return context.get("url", "/")
