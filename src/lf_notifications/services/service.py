from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence
from django.db import transaction
from beach_wood_user.models import BWUser
from lf_notifications.models import (
    Notification,
    NotificationRecipient,
    NotificationPreference,
    NotificationVerb,
    NotificationProxy,
    NotificationChannelChoices,
)
from lf_notifications.services.registry import NotificationRegistry, BaseNotificationType

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Central service for triggering and managing notifications.
    """

    @classmethod
    @transaction.atomic
    def trigger(
        cls,
        notification_type_name: str,
        actor: Optional[BWUser] = None,
        recipients: Sequence[BWUser] = (),
        verb: str = NotificationVerb.CREATED,
        context: Optional[Dict[str, Any]] = None,
        content_object: Optional[Any] = None,
    ) -> Optional[NotificationProxy]:
        """
        Triggers a notification event.
        """
        context = context or {}
        try:
            notification_type = NotificationRegistry.get_type(notification_type_name)
        except KeyError:
            logger.error(f"Notification type '{notification_type_name}' not found.")
            return None

        # 1. Create the main Notification record
        message = notification_type.get_message(context)
        
        notification = Notification.objects.create(
            actor=actor,
            verb=verb,
            message_template=message,
            content_object=content_object,
            metadata=context.get("metadata", {}),
        )
        notification_proxy = NotificationProxy.objects.get(pk=notification.pk)

        # 2. Process each recipient
        for recipient in recipients:
            # Create the recipient record (In-App database channel)
            NotificationRecipient.objects.create(
                notification=notification_proxy,
                recipient=recipient,
            )

            # 3. Resolve channels and check preferences
            enabled_channels = cls._resolve_channels(recipient, notification_type)
            
            for channel_name in enabled_channels:
                try:
                    channel = NotificationRegistry.get_channel(channel_name)
                    # For in_app, it's already "sent" by creating the NotificationRecipient record
                    if channel_name != "in_app":
                        channel.send(recipient, notification_proxy, context)
                except Exception as e:
                    logger.exception(f"Failed to send notification via channel '{channel_name}': {e}")

        return notification_proxy

    @classmethod
    def _resolve_channels(
        cls, 
        recipient: BWUser, 
        notification_type: type[BaseNotificationType]
    ) -> List[str]:
        """
        Determines which channels are enabled for a user and notification type.
        """
        default_channels = notification_type.default_channels
        
        # Query user preferences
        prefs = NotificationPreference.objects.filter(
            user=recipient,
            notification_type=notification_type.name,
        ).values_list("channel", "enabled")
        
        pref_map = {channel: enabled for channel, enabled in prefs}
        
        resolved_channels = []
        for channel in NotificationChannelChoices.values:
            # If explicit preference exists, use it
            if channel in pref_map:
                if pref_map[channel]:
                    resolved_channels.append(channel)
            # Otherwise use default if channel is in defaults
            elif channel in default_channels:
                resolved_channels.append(channel)
                
        return resolved_channels
