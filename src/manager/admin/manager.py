# -*- coding: utf-8 -*-#
from django.contrib import admin

from manager.models import ManagerProxy
from core.admin import BWBaseAdminModelMixin


@admin.register(ManagerProxy)
class ManagerAdmin(BWBaseAdminModelMixin):
    list_filter = [] + BWBaseAdminModelMixin.list_filter
    list_display = ["user__email", "is_deleted", "created_at"]
