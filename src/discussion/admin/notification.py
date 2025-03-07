# -*- coding: utf-8 -*-#

from django.contrib import admin

from core.admin import BWBaseAdminModelMixin
from discussion.models import DiscussionNotification


@admin.register(DiscussionNotification)
class DiscussionNotificationAdmin(BWBaseAdminModelMixin):
    list_display = [
        "msg",
        "special_assignment",
        "job",
        "recipient",
        "is_read",
        "created_at",
    ]
    readonly_fields = ["is_read"]
