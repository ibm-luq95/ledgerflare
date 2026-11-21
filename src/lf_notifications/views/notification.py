"""API ViewSets for user notifications."""
from __future__ import annotations

from typing import Any, ClassVar

from django.db.models import QuerySet
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from lf_notifications.models import NotificationRecipientProxy
from lf_notifications.serializers.notification import NotificationRecipientSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """API endpoint allowing authenticated users to manage their notifications."""

    serializer_class = NotificationRecipientSerializer
    permission_classes: ClassVar[tuple[type[permissions.BasePermission], ...]] = (
        permissions.IsAuthenticated,
    )
    filterset_fields: ClassVar[list[str]] = [
        "is_read",
        "notification__notification_type",
    ]
    search_fields: ClassVar[list[str]] = ["notification__verb"]
    ordering_fields: ClassVar[list[str]] = ["created_at", "read_at"]
    ordering: ClassVar[list[str]] = ["-created_at"]

    def get_queryset(self) -> QuerySet[NotificationRecipientProxy]:
        """Ensure users can only see their own notifications."""
        return NotificationRecipientProxy.objects.filter(
            recipient=self.request.user
        ).select_related(
            "notification", "notification__actor", "notification__content_type"
        )

    @action(detail=True, methods=["post"])
    def mark_read(self, request: Request, pk: str | None = None) -> Response:
        """Mark a specific notification as read."""
        notification_recipient = self.get_object()
        notification_recipient.mark_as_read()
        return Response({"status": "notification marked as read"})

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request: Request) -> Response:
        """Mark all unread notifications as read for requesting user."""
        self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now(),
        )
        return Response({"status": "all notifications marked as read"})

    @action(detail=False, methods=["get"])
    def unread_count(self, request: Request) -> Response:
        """Return total unread notifications count for requesting user."""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"unread_count": count})

