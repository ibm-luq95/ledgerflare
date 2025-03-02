# -*- coding: utf-8 -*-#
from django.db.models import Q

from core.constants.status_labels import CON_COMPLETED, CON_ARCHIVED
from core.models.managers import SoftDeleteManager
from core.models.querysets import BaseQuerySetMixin


class JobManager(SoftDeleteManager):
    def get_queryset(self) -> BaseQuerySetMixin:
        """
        Returns a queryset of all instances of the model that are not marked as deleted.

        Returns:
            BaseQuerySetMixin: A queryset of instances of the model that are not marked as deleted.

        """
        queryset = super().get_queryset()
        # Add your custom filters
        queryset = queryset.exclude(status__in=[CON_ARCHIVED, CON_COMPLETED])
        return queryset
