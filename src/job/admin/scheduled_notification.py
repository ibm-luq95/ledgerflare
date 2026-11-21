from django.contrib import admin

from core.admin import BWBaseAdminModelMixin
from job.models import ScheduledNotification


@admin.register(ScheduledNotification)
class ScheduledNotificationAdmin(BWBaseAdminModelMixin):
    pass
