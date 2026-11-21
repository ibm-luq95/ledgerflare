# -*- coding: utf-8 -*-#
import click
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from django.db import transaction

from django.db.models import Q
from django.utils import timezone

from core.constants.status_labels import (
    CON_PAST_DUE,
    CON_COMPLETED,
    CON_ARCHIVED,
    CON_DRAFT,
)
from core.utils import bw_log
from job.models import JobProxy
from lf_notifications.services import NotificationService
from lf_notifications.models import NotificationVerb
import logging

# Apply basic config for all loggers.
# logging.basicConfig(
#     level=logging.DEBUG,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     datefmt="%m/%d/%Y %I:%M:%S %p",
# )
#
# logger = logging.getLogger("apscheduler")
# logger.setLevel(logging.DEBUG)
#
# # Add a console handler for the 'apscheduler' logger.
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(
#     logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# )
# console_handler.setLevel(logging.INFO)
# logger.addHandler(console_handler)
# print(settings.TIME_ZONE)
# print(timezone.now().strftime("%I:%M %p"))
# print(timezone.now().today().date())


def trigger_fired():
    try:
        with transaction.atomic():
            q = (
                Q(due_date__lt=timezone.now().today().date())
                | Q(due_date=timezone.now().today().date())
            ) & ~Q(status__in=[CON_ARCHIVED, CON_COMPLETED, CON_PAST_DUE, CON_DRAFT])
            all_jobs = JobProxy.objects.select_related().filter(q)
            # debugging_print(str(all_jobs.query))
            # debugging_print(f"Total not past due jobs: {len(all_jobs)}")
            if all_jobs:
                for job in all_jobs:
                    job.status = CON_PAST_DUE
                    job.updated_by_cron = True
                    job.save()

                    # Prepare recipients: manager and discussion participants
                    recipients = []
                    if job.managed_by:
                        recipients.append(job.managed_by)

                    staff_discussions = job.get_staff_discussions()
                    if staff_discussions:
                        for staff in staff_discussions:
                            if staff not in recipients:
                                recipients.append(staff)

                    if recipients:
                        NotificationService.trigger(
                            notification_type_name="job_past_due",
                            verb=NotificationVerb.STATUS_CHANGED,
                            recipients=recipients,
                            content_object=job,
                            context={
                                "job_title": job.title,
                                "url": job.get_absolute_url(),
                            },
                        )

    except Exception as ex:
        bw_log().print_exception(suppress=[click], show_locals=False)


def check_past_due_jobs():
    """Check if any jobs are past due."""
    try:
        scheduler = BackgroundScheduler()
        cron_trigger = CronTrigger(
            year="*",
            month="*",
            day="*",
            hour=7,
            minute=0,
            timezone=settings.TIME_ZONE,
            # year="*",
            # month="*",
            # day="*",
            # hour=14,
            # minute=28,
            # timezone=settings.TIME_ZONE,
        )
        # scheduler.add_job(
        #     trigger_fired,
        #     "cron",
        #     hour=22,
        #     minute=37,
        #     # day="*",
        #     # month="*",
        #     # second="*",
        #     # year="*",
        #     id="check_past_due_jobs",
        #     replace_existing=True,
        #     timezone=settings.TIME_ZONE,
        # )
        scheduler.add_job(
            trigger_fired,
            trigger=cron_trigger,
            id="check_past_due_jobs",
            replace_existing=True,
        )
        scheduler.start()
    except Exception as ex:
        bw_log().print_exception(suppress=[click], show_locals=False)
        scheduler.shutdown()


def check_scheduled_trigger_fired():
    print("CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC")
    print("################################\n")


def check_scheduled_jobs():
    try:
        """Check if any jobs are past due."""
        scheduler = BackgroundScheduler()
        cron_trigger = CronTrigger(
            year="*",
            month="*",
            day="*",
            hour="*",
            minute="*",
            second=10,
            timezone=settings.TIME_ZONE,
        )
        scheduler.configure(timezone="UTC")
        # scheduler.scheduled_job(args=check_scheduled_trigger_fired, trigger=cron_trigger)
        scheduler.add_job(
            check_scheduled_trigger_fired,
            cron_trigger,
            # seconds=10,
            # coalesce=True,
            id="check_scheduled_jobs",
            replace_existing=True,
            max_instances=1,
            # name="sdflsdfjds",
            # misfire_grace_time=60,
        )
        scheduler.start()
    except Exception as ex:
        bw_log().print_exception(suppress=[click], show_locals=False)
        scheduler.shutdown()
