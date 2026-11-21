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
from special_assignment.models import SpecialAssignmentProxy


# print(settings.TIME_ZONE)
# print(timezone.now().strftime("%I:%M %p"))
# print(timezone.now().today().date())


def trigger_fired():
    try:
        with transaction.atomic():
            q = (
                Q(due_date__lt=timezone.now().today().date())
                | Q(due_date=timezone.now().today().date())
            ) & ~Q(status__in=[CON_ARCHIVED, CON_COMPLETED, CON_PAST_DUE])
            all_sas = SpecialAssignmentProxy.objects.select_related().filter(q)
            if all_sas:
                for sa in all_sas:
                    sa.status = CON_PAST_DUE
                    sa.updated_by_cron = True
                    sa.save()

    except Exception as ex:
        bw_log().print_exception(suppress=[click], show_locals=False)


def check_past_due_sa():
    """Check if any jobs are past due."""
    scheduler = BackgroundScheduler()
    cron_trigger = CronTrigger(
        year="*",
        month="*",
        day="*",
        hour=8,
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
        id="check_past_due_sa",
        replace_existing=True,
    )
    scheduler.start()
