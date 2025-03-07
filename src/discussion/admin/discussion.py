# -*- coding: utf-8 -*-#
import textwrap

from django.contrib import admin

from core.admin import BWBaseAdminModelMixin
from discussion.models import DiscussionProxy


@admin.register(DiscussionProxy)
class DiscussionAdmin(BWBaseAdminModelMixin):
    list_display = [
        "body",
        "attachment",
        "has_replies",
        "special_assignment",
        "sender",
        "job",
        "created_at",
    ]
    readonly_fields = ["is_seen"]

    @admin.display(description="Has Replies")
    def has_replies(self, obj: DiscussionProxy):
        if obj.replies:
            return textwrap.shorten(obj.replies.body, width=50, placeholder="...")
        return None
