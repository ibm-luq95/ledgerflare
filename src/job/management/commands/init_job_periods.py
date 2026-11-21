# -*- coding: utf-8 -*-#
import traceback
from datetime import datetime, date

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import gettext as _

from core.management.mixins import CommandStdOutputMixin
from core.utils.developments.debugging_prompt import DebuggingPrompt
from job.models import JobProxy


class Command(BaseCommand, CommandStdOutputMixin):
    help = _("Init job months and years periods")

    def add_arguments(self, parser):
        parser.add_argument(
            "--date-field",
            "-d",
            type=str,
            help=_(
                "Pick the date field start date or created date field, ie: start_date or created_date"
            ),
            required=True,
        )

    def handle(self, *args, **options):
        try:
            date_field = options.get("date_field")
            if date_field not in ["start_date", "created_date"]:
                self.stdout_output("error", _("Date field not valid"))
                return
            date_field_label = (
                "start_date" if date_field == "start_date" else "created_at"
            )
            self.stdout_output("warn", _("Init job months and years periods"))
            all_jobs = JobProxy.original_objects.all()
            cnfm = DebuggingPrompt.confirm(_("Are you sure want to start?"))
            if cnfm is True:
                with transaction.atomic():
                    for job in all_jobs:
                        job_date_field: datetime | date = getattr(job, date_field_label)
                        if job_date_field:
                            # DebuggingPrint.print(str(job_date_field.year))
                            # DebuggingPrint.print(str(job_date_field.month))
                            job.period_year = str(job_date_field.year)
                            # job.period_year = None
                            job.period_month = str(job_date_field.month)
                            # job.period_month = None
                            job.save()
                            self.stdout_output("warn", _(f"Job {job.pk} saved"))
                        else:
                            self.stdout_output(
                                "error", _(f"Job {job.pk} date field not found")
                            )
            else:
                return
        except Exception as ex:
            self.stdout_output("error", traceback.format_exc())
