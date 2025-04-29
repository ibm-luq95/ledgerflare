# -*- coding: utf-8 -*-#
from django.contrib import admin

from bookkeeper.models import BookkeeperProxy
from core.admin import BWBaseAdminModelMixin


@admin.register(BookkeeperProxy)
class BookkeeperAdmin(BWBaseAdminModelMixin):
    # list_filter = [] + BWBaseAdminModelMixin.list_filter
    list_display = ["user__email", "is_deleted", "created_at"]
