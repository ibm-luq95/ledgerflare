# -*- coding: utf-8 -*-#
"""
File: documents.py
Author: Ibrahim Luqman
Date: 5/10/24

Description: Choices for the document app
"""
from django.db import models
from django.utils.translation import gettext as _
import inflection

from core.constants.general import CON_CLIENT, CON_JOB, CON_TASK


class DocumentSectionEnum(models.TextChoices):
    CLIENT = CON_CLIENT, _(inflection.humanize(CON_CLIENT))
    JOB = CON_JOB, _(inflection.humanize(CON_JOB))
    TASK = CON_TASK, _(inflection.humanize(CON_TASK))
