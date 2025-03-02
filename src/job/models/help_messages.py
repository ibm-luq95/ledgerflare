# -*- coding: utf-8 -*-#
from django.utils.translation import gettext as _

JOB_HELP_MESSAGES = {
    "bookkeeper": _("Bookkeeper of the job"),
    "assistant": _("Assistant(s) of the job"),
    "title": _("Job Title"),
    "note": _("Note(s) for this job (optional)"),
    "job_type": _("Type of this job, Recurring, Weekly, Urgent,..etc"),
    "status": _("Status of this job, Not Started, In Progress, Done,..etc"),
    "client": _("Client this job belong to"),
    "tasks": _("Tasks of this job"),
    "description": _("Description of the job"),
    "due_date": _("Due date for this job"),
    "managed_by": _("Staff member who will handle the job"),
    "state": _("Job state"),
    "categories": _("Categorize your job"),
    "period_year": _("Period year which will be used in reporting"),
    "period_month": _("Period month which will be used in reporting"),
    "is_scheduled": _("Set the start date as scheduled date"),
    "scheduled_date": _("Scheduled date which bookkeeper start working on the job"),
}
