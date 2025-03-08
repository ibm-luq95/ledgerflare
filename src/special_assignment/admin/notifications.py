# -*- coding: utf-8 -*-#
from django.contrib import admin

from core.admin import BWBaseAdminModelMixin
from special_assignment.models import SpecialAssignmentNotification


@admin.register(SpecialAssignmentNotification)
class SpecialAssignmentNotificationAdmin(BWBaseAdminModelMixin):
    list_filter = (
        "is_read",
        "recipient",
        "special_assignment",
    )
    list_display = (
        "special_assignment",
        "msg",
        "recipient",
        "is_read",
        "created_at",
    )
