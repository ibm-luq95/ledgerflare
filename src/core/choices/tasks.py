# -*- coding: utf-8 -*-#
"""
File: tasks.py
Author: Ibrahim Luqman
Date: 5/10/24

Description: Task's choices
"""
import inflection
from django.db import models
from django.utils.translation import gettext as _

from core.constants.status_labels import (
    CON_ARCHIVED,
    CON_COMPLETED,
    CON_IN_PROGRESS,
    CON_NOT_STARTED,
    CON_DRAFT,
    CON_NOT_COMPLETED,
    CON_PAST_DUE,
)
from core.constants.types_labels import (
    CON_NO_TYPE,
    CON_RECURRING,
    CON_WEEKLY,
    CON_MONTHLY,
    CON_QUARTERLY,
    CON_YEARLY,
    CON_ONE_TIME,
    CON_URGENT,
)


class TaskStatusEnum(models.TextChoices):
    NOT_STARTED = CON_NOT_STARTED, _(inflection.humanize(CON_NOT_STARTED))
    IN_PROGRESS = CON_IN_PROGRESS, _(inflection.humanize(CON_IN_PROGRESS))
    COMPLETED = CON_COMPLETED, _(inflection.humanize(CON_COMPLETED))
    NOT_COMPLETED = CON_NOT_COMPLETED, _(inflection.humanize(CON_NOT_COMPLETED))
    PAST_DUE = CON_PAST_DUE, _(inflection.humanize(CON_PAST_DUE))
    ARCHIVED = CON_ARCHIVED, _(inflection.humanize(CON_ARCHIVED))
    DRAFT = CON_DRAFT, _(inflection.humanize(CON_DRAFT))


class TaskTypeEnum(models.TextChoices):
    NO_TYPE = CON_NO_TYPE, _(inflection.humanize(CON_NO_TYPE))
    RECURRING = CON_RECURRING, _(inflection.humanize(CON_RECURRING))
    WEEKLY = CON_WEEKLY, _(inflection.humanize(CON_WEEKLY))
    MONTHLY = CON_MONTHLY, _(inflection.humanize(CON_MONTHLY))
    QUARTERLY = CON_QUARTERLY, _(inflection.humanize(CON_QUARTERLY))
    YEARLY = CON_YEARLY, _(inflection.humanize(CON_YEARLY))
    ONE_TIME = CON_ONE_TIME, _(inflection.humanize(CON_ONE_TIME))
    URGENT = CON_URGENT, _(inflection.humanize(CON_URGENT))
