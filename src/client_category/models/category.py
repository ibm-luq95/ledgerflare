from typing import ClassVar

from django.db import models
from django.utils.translation import gettext as _

from core.models.mixins import BaseModelMixin
from core.models.mixins import GeneralStatusFieldMixin
from core.models.mixins import StrModelMixin


class ClientCategory(BaseModelMixin, GeneralStatusFieldMixin, StrModelMixin):
    name = models.CharField(_("name"), max_length=50, db_index=True, unique=True)

    class Meta(BaseModelMixin.Meta):
        ordering: ClassVar[list[str]] = ["name"]
