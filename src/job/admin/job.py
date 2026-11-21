# -*- coding: utf-8 -*-#
from django.contrib import admin
from django.db import transaction
from django.utils.translation import gettext as _

from core.constants.status_labels import CON_DRAFT, CON_COMPLETED, CON_ARCHIVED
from job.models import JobProxy
from core.admin import BWBaseAdminModelMixin


@admin.register(JobProxy)
class JobAdmin(BWBaseAdminModelMixin):
    actions = ["make_draft", "make_completed", "make_archived"]
    search_fields = ("title", "client", "status", "managed_by", "state", "job_type")
    list_filter = (
        "status",
        "state",
        "job_type",
        "period_year",
        "period_month",
        "managed_by",
        # "client",
    )
    list_per_page = 20
    list_display = (
        "title",
        "client",
        "job_type",
        "status",
        "period_year",
        "period_month",
        "start_date",
        "due_date",
        "state",
        "managed_by",
        "updated_by_cron",
        "created_at",
    )

    @admin.action(description=_("Mark selected job as draft"))
    def make_draft(self, request, queryset):
        try:
            with transaction.atomic():
                queryset.update(status=CON_DRAFT)
            self.message_user(request, _("Job(s) marked as draft."), level="success")
        except Exception as ex:
            self.message_user(request, str(ex), level="error")

    @admin.action(description=_("Mark selected job as completed"))
    def make_completed(self, request, queryset):
        try:
            with transaction.atomic():
                queryset.update(status=CON_COMPLETED)
            self.message_user(
                request, _("Job(s) marked as completed."), level="success"
            )
        except Exception as ex:
            self.message_user(request, str(ex), level="error")

    @admin.action(description=_("Mark selected job as archived"))
    def make_archived(self, request, queryset):
        try:
            with transaction.atomic():
                queryset.update(status=CON_ARCHIVED)
            self.message_user(request, _("Job(s) marked as archived."), level="success")
        except Exception as ex:
            self.message_user(request, str(ex), level="error")

    class Media:
        js = ["admin/js/jquery.init.js", "js/admin/job.js"]
