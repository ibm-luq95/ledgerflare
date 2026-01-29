# -*- coding: utf-8 -*-#

import uuid
from typing import Optional

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _

from core.models.managers import SoftDeleteManager
from .diffing import DiffingMixin
from .get_model_instance_as_dict import GetModelInstanceAsDictMixin
from ..managers.archive_manager import ArchiveManager


class BaseModelMixin(DiffingMixin, GetModelInstanceAsDictMixin, models.Model):
    """
    A mixin class that provides common functionality for models in the LedgerFlar
    Financial application.

    This mixin class includes fields and methods that are commonly used by models.

    Fields:
    - id: A UUID field that serves as the primary key for the model.
    - metadata: A JSONField that stores additional metadata for the model.
    - is_deleted: A Boolean field that indicates whether the model is deleted or not.
    - created_at: A DateTimeField that stores the timestamp when the model was created.
    - updated_at: A DateTimeField that stores the timestamp when the model was last updated.
    - deleted_at: A DateTimeField that stores the timestamp when the model was deleted (if applicable).

    Methods:
    - get_columns_names: A class method that returns the names of the columns for the model.
      It takes optional parameters `fields` and `excluded` to specify which fields to include or exclude from the column names.
    - soft_delete: A method that marks the model as deleted by setting the `is_deleted` field to `True` and recording the deletion timestamp.
    - hard_delete: A method that permanently deletes the model from the database by calling the `delete` method on the `original_objects` manager.
    - delete: A method that performs a soft delete by calling the `soft_delete` method.
    - restore: A method that restores a deleted model by setting the `is_deleted` field to `False` and clearing the deletion timestamp.

    The `BaseModelMixin` class also includes a `Meta` class with the following attributes:
    - abstract = True: This indicates that the `BaseModelMixin` class is intended to be used as a base class for other models and should not be instantiated directly.
    - permissions: A list of permission tuples that define the permissions available for the models using this mixin.
      The permissions include "can_view_list" and "view_archive".

    Overall, the `BaseModelMixin` class provides a foundation for models in the Beachwood Wood Financial application by defining common fields and methods,
    and specifying metadata and permissions.

    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metadata = models.JSONField(
        _("metadata"), null=True, blank=True, default=dict, editable=False
    )
    is_deleted = models.BooleanField(_("is deleted"), default=False, editable=False)
    created_at = models.DateTimeField(
        _("created at"), default=timezone.now, editable=False
    )
    updated_at = models.DateTimeField(
        _("updated at"), auto_now=True, blank=True, null=True, editable=False
    )
    deleted_at = models.DateTimeField(
        _("deleted at"), null=True, default=None, blank=True, editable=False
    )

    objects: SoftDeleteManager = SoftDeleteManager()
    # objects = models.Manager()
    original_objects: models.Manager = models.Manager()
    archive_objects: ArchiveManager = ArchiveManager()

    class Meta:
        abstract = True
        # base_manager_name = "objects"
        # ordering = ["-created_at", "-updated_at"]
        # ordering = ["-created_at"]
        permissions = [
            ("can_view_list", "Can view list view"),
            ("view_archive", "Can view archive"),
        ]

    @classmethod
    def get_columns_names(
        cls, fields: Optional[list | tuple] = None, excluded: Optional[list | tuple] = None
    ) -> list | tuple:
        """
        Get the names of the columns for the model.

        Args:
            fields (Optional[list | tuple], optional): A list or tuple of fields to include in the column names. Defaults to None.
            excluded (Optional[list | tuple], optional): A list or tuple of fields to exclude from the column names. Defaults to None.

        Returns:
            list | tuple: A list or tuple of the column names.

        """
        columns_names = []
        excluded_fields = ["id", "metadata", "deleted_at", "updated_at", "is_deleted"]
        if excluded is not None:
            excluded_fields = excluded_fields + excluded
        for field in cls._meta.get_fields():
            if field.name not in excluded_fields:
                columns_names.insert(0, field.verbose_name)
        return columns_names

    # def soft_delete(self):
    #     """
    #     Marks the model as deleted by setting the `is_deleted` field to `True` and
    #     recording the deletion timestamp.
    #     """
    #     self.is_deleted = True
    #     self.deleted_at = timezone.now()
    #     self.save()
    #
    def hard_delete(self):
        """
        Marks the model as deleted by calling the `delete` method on the `original_objects`
        manager.
        """
        self.original_objects.delete()

    def delete(self):
        """
        Soft delete the object.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """
        Restore the soft-deleted object.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save()
