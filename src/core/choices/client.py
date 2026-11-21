# -*- coding: utf-8 -*-#
"""
File: client.py
Author: Ibrahim Luqman
Date: 5/10/24

Description: Client status enum
"""
import inflection
from django.db import models
from django.utils.translation import gettext as _

from core.constants.status_labels import CON_ENABLED, CON_DISABLED, CON_ARCHIVED


class ClientStatusEnum(models.TextChoices):
    ENABLED = CON_ENABLED, _(inflection.humanize(CON_ENABLED))
    DISABLED = CON_DISABLED, _(inflection.humanize(CON_DISABLED))
    ARCHIVE = CON_ARCHIVED, _(inflection.humanize(CON_ARCHIVED))
