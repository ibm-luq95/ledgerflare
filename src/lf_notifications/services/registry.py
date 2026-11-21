from __future__ import annotations

from typing import Any, Type, Dict, List
from django.utils.translation import gettext_lazy as _

class BaseNotificationType:
    """
    Abstract base class that all notification types must implement.
    """
    name: str = ""
    verbose_name: str = ""
    default_channels: List[str] = ["in_app"]

    @classmethod
    def get_message(cls, context: Dict[str, Any]) -> str:
        """
        Returns the message string for in-app or simple channels.
        """
        return str(context.get("message", ""))

    @classmethod
    def get_email_subject(cls, context: Dict[str, Any]) -> str:
        """
        Returns the email subject line.
        """
        return str(context.get("subject", _("Notification Alert")))

    @classmethod
    def get_email_template(cls, context: Dict[str, Any]) -> str:
        """
        Returns the path to the HTML template.
        """
        return "notifications/emails/base.html"

    @classmethod
    def get_action_url(cls, context: Dict[str, Any]) -> str:
        """
        Returns the redirect URL for when a user clicks the notification.
        """
        return "/"

class NotificationRegistry:
    """
    Registry for notification types and delivery channels.
    """
    _types: Dict[str, Type[BaseNotificationType]] = {}
    _channels: Dict[str, Any] = {}

    @classmethod
    def register_type(cls, notification_type: Type[BaseNotificationType]) -> Type[BaseNotificationType]:
        if not notification_type.name:
            raise ValueError(f"Notification type {notification_type.__name__} must have a 'name' attribute.")
        cls._types[notification_type.name] = notification_type
        return notification_type

    @classmethod
    def register_channel(cls, channel_name: str, channel_class: Any) -> Any:
        cls._channels[channel_name] = channel_class
        return channel_class

    @classmethod
    def get_type(cls, name: str) -> Type[BaseNotificationType]:
        if name not in cls._types:
            raise KeyError(f"Notification type '{name}' is not registered.")
        return cls._types[name]

    @classmethod
    def get_all_types(cls) -> Dict[str, Type[BaseNotificationType]]:
        return cls._types

    @classmethod
    def get_channel(cls, name: str) -> Any:
        if name not in cls._channels:
            raise KeyError(f"Channel '{name}' is not registered.")
        return cls._channels[name]

    @classmethod
    def get_all_channels(cls) -> Dict[str, Any]:
        return cls._channels

def register_notification_type(notification_type: Type[BaseNotificationType]) -> Type[BaseNotificationType]:
    """
    Decorator for registering notification types.
    """
    return NotificationRegistry.register_type(notification_type)
