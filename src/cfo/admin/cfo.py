from django.contrib import admin

from cfo.models import CFOProxy
from core.admin import BWBaseAdminModelMixin


@admin.register(CFOProxy)
class CFOAdmin(BWBaseAdminModelMixin):
    list_filter = [] + BWBaseAdminModelMixin.list_filter
    list_display = ["user", "user__email", "is_deleted", "created_at"]
