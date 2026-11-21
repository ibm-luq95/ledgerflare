from __future__ import annotations

from typing import Any, Dict, List, Optional
from django.db import transaction
from beach_wood_user.models import BWUser
from lf_notifications.models import (
    Notification,
    NotificationRecipient,
    NotificationPreference,
    NotificationVerb,
    NotificationProxy,
)
from lf_notifications.services.registry import NotificationRegistry

class BaseNotificationChannel:
    """
    Abstract interface for delivery channels.
    """
    channel_name: str = ""

    @classmethod
    def send(
        cls,
        recipient: BWUser,
        notification: NotificationProxy,
        context: Dict[str, Any],
    ) -> bool:
        """
        Dispatches the notification to the target recipient.
        """
        raise NotImplementedError("Subclasses must implement send()")

class InAppNotificationChannel(BaseNotificationChannel):
    channel_name = "in_app"

    @classmethod
    def send(
        cls,
        recipient: BWUser,
        notification: NotificationProxy,
        context: Dict[str, Any],
    ) -> bool:
        """
        In-app notifications are created in the database during the trigger process.
        This channel acts as a confirmation that the in-app record exists.
        """
        return True

class EmailNotificationChannel(BaseNotificationChannel):
    channel_name = "email"

    @classmethod
    def send(
        cls,
        recipient: BWUser,
        notification: NotificationProxy,
        context: Dict[str, Any],
    ) -> bool:
        # Placeholder for actual email sending logic (e.g., using django.core.mail)
        # In a real implementation, this would use the templates from the notification type.
        return True

# Register default channels
NotificationRegistry.register_channel("in_app", InAppNotificationChannel)
NotificationRegistry.register_channel("email", EmailNotificationChannel)
