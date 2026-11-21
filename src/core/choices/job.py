# -*- coding: utf-8 -*-#
"""
File: job.py
Author: Ibrahim Luqman
Date: 5/10/24

Description: Job app's choices
"""
import inflection
from django.db import models
from django.utils.translation import gettext as _

from core.constants.status_labels import (
    CON_NOT_STARTED,
    CON_ARCHIVED,
    CON_IN_PROGRESS,
    CON_PAST_DUE,
    CON_COMPLETED,
    CON_NOT_COMPLETED,
    CON_DRAFT,
    CON_NEED_INFO,
    CON_STALLED,
    CON_ONGOING,
)
from core.constants.types_labels import (
    CON_NO_TYPE,
    CON_RECURRING,
    CON_URGENT,
    CON_WEEKLY,
    CON_YEARLY,
    CON_MONTHLY,
    CON_QUARTERLY,
    CON_ONE_TIME,
)


class JobTypeEnum(models.TextChoices):
    NO_TYPE = CON_NO_TYPE, _(inflection.humanize(CON_NO_TYPE))
    RECURRING = CON_RECURRING, _(inflection.humanize(CON_RECURRING))
    WEEKLY = CON_WEEKLY, _(inflection.humanize(CON_WEEKLY))
    MONTHLY = CON_MONTHLY, _(inflection.humanize(CON_MONTHLY))
    QUARTERLY = CON_QUARTERLY, _(inflection.humanize(CON_QUARTERLY))
    YEARLY = CON_YEARLY, _(inflection.humanize(CON_YEARLY))
    ONE_TIME = CON_ONE_TIME, _(inflection.humanize(CON_ONE_TIME))
    URGENT = CON_URGENT, _(inflection.humanize(CON_URGENT))


class JobStatusEnum(models.TextChoices):
    NOT_STARTED = CON_NOT_STARTED, _(inflection.humanize(CON_NOT_STARTED))
    IN_PROGRESS = CON_IN_PROGRESS, _(inflection.humanize(CON_IN_PROGRESS))
    PAST_DUE = CON_PAST_DUE, _(inflection.humanize(CON_PAST_DUE))
    COMPLETED = CON_COMPLETED, _(inflection.humanize(CON_COMPLETED))
    NOT_COMPLETED = CON_NOT_COMPLETED, _(inflection.humanize(CON_NOT_COMPLETED))
    ARCHIVED = CON_ARCHIVED, _(inflection.humanize(CON_ARCHIVED))
    DRAFT = CON_DRAFT, _(inflection.humanize(CON_DRAFT))


class JobStateEnum(models.TextChoices):
    NEED_INFO = CON_NEED_INFO, _(inflection.humanize(CON_NEED_INFO))
    STALLED = CON_STALLED, _(inflection.humanize(CON_STALLED))
    ONGOING = CON_ONGOING, _(inflection.humanize(CON_ONGOING))
