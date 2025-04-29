# -*- coding: utf-8 -*-#
from random import randint
from typing import Any

from django.db import models
from django.db.models import Q, QuerySet, Model
from django.db.models.aggregates import Count

from core.constants.status_labels import CON_COMPLETED, CON_ARCHIVED
from core.models.querysets import BaseQuerySetMixin


class SoftDeleteManager(models.Manager):
    """
    A custom manager for models with a soft delete feature.

    This manager provides methods for querying instances that are not marked as deleted.
    It also includes additional methods for random selection and filtering by status.

    Methods:
        get_queryset(self) -> BaseQuerySetMixin: Returns a `BaseQuerySetMixin` object representing all instances of the model that are not marked as deleted.
        all(self) -> BaseQuerySetMixin: Returns a `BaseQuerySetMixin` object representing all instances of the model with a status not in `ALLOWED_STATUS`.
        random(self) -> Model: Returns a random instance of the model that is not marked as deleted.

    Attributes:
        ALLOWED_STATUS (list): A list of status values that are considered allowed and not marked as deleted.

    """

    ALLOWED_STATUS = [CON_ARCHIVED, CON_COMPLETED]

    # def get_queryset(self) -> BaseQuerySetMixin:
    #     """
    #     Returns a queryset of all instances of the model that are not marked as deleted.
    #
    #     Returns:
    #         BaseQuerySetMixin: A queryset of instances of the model that are not marked as deleted.
    #
    #     """
    #     queryset = BaseQuerySetMixin(self.model, using=self._db).filter(
    #         Q(is_deleted=False)
    #     )
    #
    #     return queryset

    def get_queryset(self):
        """
        Return a custom QuerySet that excludes soft-deleted rows by default.
        """
        return BaseQuerySetMixin(self.model, using=self._db).filter(is_deleted=False)

    def all(self) -> QuerySet[Any, Any] | QuerySet[Model | Any, Any]:
        """
        Returns a `BaseQuerySetMixin` object representing all instances of the model with a
        status of either `CON_ARCHIVED` or `CON_COMPLETED`, ordered by `created_at` in
        descending order.

        Args:
            self: The instance of the class.

        Returns:
            A `BaseQuerySetMixin` object representing all instances of the model with the specified statuses.

        """
        qs = self.get_queryset()
        field_names = [field.name for field in self.model._meta.fields]
        if "status" in field_names:
            qs = qs.filter(~Q(status__in=self.ALLOWED_STATUS))
        return qs

    def delete(self):
        """
        Soft delete all objects in the queryset.
        """
        return self.get_queryset().delete()

    def restore(self):
        """
        Restore all soft-deleted objects in the queryset.
        """
        return self.get_queryset().restore()
