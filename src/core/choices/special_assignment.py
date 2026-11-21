# -*- coding: utf-8 -*-#
"""
File: special_assignment.py
Author: Ibrahim Luqman
Date: 5/10/24

Description: Special assignment's choices
"""
import inflection
from django.db import models
from django.utils.translation import gettext as _

from core.constants.status_labels import (
    CON_NOT_STARTED,
    CON_COMPLETED,
    CON_IN_PROGRESS,
    CON_ARCHIVED,
    CON_REJECTED,
    CON_PAST_DUE,
)


class SpecialAssignmentStatusEnum(models.TextChoices):
    NOT_STARTED = CON_NOT_STARTED, _(inflection.humanize(CON_NOT_STARTED))
    IN_PROGRESS = CON_IN_PROGRESS, _(inflection.humanize(CON_IN_PROGRESS))
    PAST_DUE = CON_PAST_DUE, _(inflection.humanize(CON_PAST_DUE))
    COMPLETED = CON_COMPLETED, _(inflection.humanize(CON_COMPLETED))
    REJECTED = CON_REJECTED, _(inflection.humanize(CON_REJECTED))
    ARCHIVED = CON_ARCHIVED, _(inflection.humanize(CON_ARCHIVED))
