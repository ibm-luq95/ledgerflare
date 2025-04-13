# -*- coding: utf-8 -*-#
from django import forms
from django.contrib import admin

from core.admin import BWBaseAdminModelMixin
from discussion.models import DiscussionProxy
from special_assignment.models import SpecialAssignmentProxy
from special_assignment.resources.special_assignment import SpecialAssignmentResource


class DiscussionInline(admin.TabularInline):
    model = DiscussionProxy
    fields = ["body", "attachment", "special_assignment"]
    extra = 1


@admin.register(SpecialAssignmentProxy)
class SpecialAssignmentAdmin(BWBaseAdminModelMixin):
    list_filter = ("status", "client", "job", "updated_by_cron")
    inlines = [DiscussionInline]
    resource_classes = [SpecialAssignmentResource]
    list_display = (
        "title",
        "client",
        "job",
        # "manager",
        "assigned_to",
        "assigned_by",
        "status",
        "is_seen",
        "attachment",
        "updated_by_cron",
        "created_at",
    )
