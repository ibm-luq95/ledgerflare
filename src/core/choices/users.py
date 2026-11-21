# -*- coding: utf-8 -*-#
"""
File: users.py
Author: Ibrahim Luqman
Date: 5/10/24

Description: beach_wood_user's choices
"""
import inflection
from django.db import models
from django.utils.translation import gettext as _

from core.constants.status_labels import (
    CON_ENABLED,
    CON_PENDING,
    CON_CANCELED,
    CON_ARCHIVED,
    CON_DISABLED,
)
from core.constants.users import (
    CON_BOOKKEEPER,
    CON_MANAGER,
    CON_ASSISTANT,
    CON_USER,
    CON_DEVELOPER,
    CON_CFO,
)


class BeachWoodUserTypeEnum(models.TextChoices):
    MANAGER = CON_MANAGER, _(inflection.humanize(CON_MANAGER))
    ASSISTANT = CON_ASSISTANT, _(inflection.humanize(CON_ASSISTANT))
    BOOKKEEPER = CON_BOOKKEEPER, _(inflection.humanize(CON_BOOKKEEPER))
    CFO = CON_CFO, _(inflection.humanize(CON_CFO))


class BeachWoodUserStatusEnum(models.TextChoices):
    ENABLED = CON_ENABLED, _(inflection.humanize(CON_ENABLED))
    PENDING = CON_PENDING, _(inflection.humanize(CON_PENDING))
    CANCELED = CON_CANCELED, _(inflection.humanize(CON_CANCELED))
    DISABLED = CON_DISABLED, _(inflection.humanize(CON_DISABLED))
    ARCHIVED = CON_ARCHIVED, _(inflection.humanize(CON_ARCHIVED))


class BeachWoodUserTypesEnum(models.TextChoices):
    DEVELOPER = CON_DEVELOPER, _(inflection.humanize(CON_DEVELOPER))
    USER = CON_USER, _(inflection.humanize(CON_USER))
