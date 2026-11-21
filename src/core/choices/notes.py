# -*- coding: utf-8 -*-#
"""
File: notes.py
Author: Ibrahim Luqman
Date: 5/10/24

Description: Note app's choices
"""
import inflection
from django.db import models
from django.utils.translation import gettext as _

from core.constants.general import CON_TASK, CON_CLIENT, CON_JOB
from core.constants.status_labels import CON_ENABLED, CON_DISABLED, CON_ARCHIVED


class NoteSectionEnum(models.TextChoices):
    CLIENT = CON_CLIENT, _(inflection.humanize(CON_CLIENT))
    JOB = CON_JOB, _(inflection.humanize(CON_JOB))
    TASK = CON_TASK, _(inflection.humanize(CON_TASK))


class NoteStatusEnum(models.TextChoices):
    ENABLED = CON_ENABLED, _(inflection.humanize(CON_ENABLED))
    DISABLED = CON_DISABLED, _(inflection.humanize(CON_DISABLED))
    ARCHIVE = CON_ARCHIVED, _(inflection.humanize(CON_ARCHIVED))
