from django.contrib import admin

from client.models import ClientProxy
from client.resources.client import ClientResource
from core.admin import BWBaseAdminModelMixin
from core.admin.tabularinline_readonly_mixin import ReadOnlyInlineMixin
from job.models import JobProxy


class JobsInline(ReadOnlyInlineMixin):
    model = JobProxy
    can_delete = False
    extra = 0
    # readonly_fields = ["title", "managed_by", "start_date", "due_date", "status"]
    fields = [
        "title",
        "managed_by",
        "period_year",
        "period_month",
        "start_date",
        "due_date",
        "status",
    ]
    save_as_continue = False


@admin.register(ClientProxy)
class ClientAdmin(BWBaseAdminModelMixin):
    list_display = ("pk", "name", "email", "industry", "status", "job_count", "created_at")
    list_filter = ["status", "bookkeepers"] + BWBaseAdminModelMixin.list_filter
    search_fields = (
        "email",
        "industry",
    )
    inlines = [JobsInline]
    readonly_fields = ["id"]
    resource_classes = [ClientResource]

    def job_count(self, obj):
        return obj.jobs.count()  # Count related jobs

    job_count.short_description = "Jobs Count"  # Column header in admin
