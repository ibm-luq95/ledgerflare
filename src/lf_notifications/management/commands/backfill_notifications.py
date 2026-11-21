from __future__ import annotations

import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.contenttypes.models import ContentType

from lf_notifications.models import Notification, NotificationRecipient, NotificationVerb, NotificationProxy
from discussion.models import DiscussionNotification
from special_assignment.models import SpecialAssignmentNotification
from job.models import ScheduledNotification

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Backfills notifications from legacy tables to the unified lf_notifications tables."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting notifications backfill..."))
        
        with transaction.atomic():
            self._backfill_discussions()
            self._backfill_special_assignments()
            self._backfill_scheduled_notifications()

        self.stdout.write(self.style.SUCCESS("Backfill completed successfully."))

    def _backfill_discussions(self):
        self.stdout.write("Backfilling Discussion notifications...")
        legacy_notifications = DiscussionNotification.objects.all()
        count = 0
        for legacy in legacy_notifications:
            # Check if already migrated
            metadata = {"legacy_source": "DiscussionNotification", "legacy_pk": str(legacy.pk)}
            if Notification.objects.filter(metadata__contains=metadata).exists():
                continue

            # Create Notification
            notification = Notification.objects.create(
                actor=legacy.discussion.sender if legacy.discussion else None,
                verb=NotificationVerb.COMMENTED,
                message_template=legacy.msg,
                content_type=ContentType.objects.get_for_model(legacy.discussion) if legacy.discussion else None,
                object_id=legacy.discussion.pk if legacy.discussion else None,
                created_at=legacy.created_at,
                metadata=metadata
            )
            notification_proxy = NotificationProxy.objects.get(pk=notification.pk)

            # Create Recipient
            NotificationRecipient.objects.create(
                notification=notification_proxy,
                recipient=legacy.recipient,
                is_read=legacy.is_read if hasattr(legacy, "is_read") else False,
                is_seen=legacy.is_seen if hasattr(legacy, "is_seen") else False,
                created_at=legacy.created_at
            )
            count += 1
        self.stdout.write(f"Migrated {count} Discussion notifications.")

    def _backfill_special_assignments(self):
        self.stdout.write("Backfilling Special Assignment notifications...")
        legacy_notifications = SpecialAssignmentNotification.objects.all()
        count = 0
        for legacy in legacy_notifications:
            metadata = {"legacy_source": "SpecialAssignmentNotification", "legacy_pk": str(legacy.pk)}
            if Notification.objects.filter(metadata__contains=metadata).exists():
                continue

            notification = Notification.objects.create(
                actor=legacy.special_assignment.assigned_by if legacy.special_assignment else None,
                verb=NotificationVerb.ASSIGNED,
                message_template=legacy.msg,
                content_type=ContentType.objects.get_for_model(legacy.special_assignment) if legacy.special_assignment else None,
                object_id=legacy.special_assignment.pk if legacy.special_assignment else None,
                created_at=legacy.created_at,
                metadata=metadata
            )
            notification_proxy = NotificationProxy.objects.get(pk=notification.pk)

            NotificationRecipient.objects.create(
                notification=notification_proxy,
                recipient=legacy.recipient,
                is_read=legacy.is_read if hasattr(legacy, "is_read") else False,
                is_seen=legacy.is_seen if hasattr(legacy, "is_seen") else False,
                created_at=legacy.created_at
            )
            count += 1
        self.stdout.write(f"Migrated {count} Special Assignment notifications.")

    def _backfill_scheduled_notifications(self):
        self.stdout.write("Backfilling Scheduled notifications...")
        legacy_notifications = ScheduledNotification.objects.all()
        count = 0
        for legacy in legacy_notifications:
            metadata = {"legacy_source": "ScheduledNotification", "legacy_pk": str(legacy.pk)}
            if Notification.objects.filter(metadata__contains=metadata).exists():
                continue

            notification = Notification.objects.create(
                actor=None,
                verb=NotificationVerb.CREATED,
                message_template=f"Job scheduled: {legacy.job.title}",
                content_type=ContentType.objects.get_for_model(legacy.job),
                object_id=legacy.job.pk,
                created_at=legacy.created_at,
                metadata=metadata
            )
            notification_proxy = NotificationProxy.objects.get(pk=notification.pk)

            NotificationRecipient.objects.create(
                notification=notification_proxy,
                recipient=legacy.user,
                is_read=False,
                is_seen=legacy.is_seen,
                created_at=legacy.created_at
            )
            count += 1
        self.stdout.write(f"Migrated {count} Scheduled notifications.")
