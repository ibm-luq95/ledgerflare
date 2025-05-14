# -*- coding: utf-8 -*-#
from django.db import models
from django.utils.translation import gettext as _

from core.choices import AssistantTypeEnum
from core.constants.users import ASSISTANT_FULL_MANAGER_PERMISSION_SHORT_NAME
from core.models.mixins import StaffMemberMixin, BaseModelMixin
from core.models.mixins.access_proxy_models_mixin import AccessProxyModelMixin


class Assistant(BaseModelMixin, StaffMemberMixin, AccessProxyModelMixin):
    """Represents an Assistant in the system.

    This class defines the model for an Assistant, including their attributes and
    permissions.

    Args:
        BaseModelMixin (models.Model): A Django base model mixin providing common
            fields and methods.
        StaffMemberMixin: A mixin for staff members providing additional functionality.
        AccessProxyModelMixin: A mixin for handling access proxy models.

    Attributes:
        assistant_type (models.CharField): The type of the assistant.
            Choices are defined in AssistantTypeEnum with a default of AssistantTypeEnum.ALL.

    Meta:
        Contains permissions associated with the Assistant.
            Permissions include access to bookkeeper and client account details,
            user editing, and full manager permissions.
    """

    """Assistant models

    Args:
        BaseModelMixin (models.Model): Django base model mixin
    """

    assistant_type = models.CharField(
        _("assistant type"),
        max_length=15,
        choices=AssistantTypeEnum.choices,
        default=AssistantTypeEnum.ALL,
    )

    # def natural_key(self) -> tuple[str]:
    #     """
    #     Return the natural key of the related BWUser for consistent serialization.
    #
    #     This ensures that relationships are preserved across fixtures and environments,
    #     even if UUIDs change.
    #
    #     Returns
    #     -------
    #     tuple[str]
    #         A single-element tuple containing the email of the associated user.
    #     """
    #     return self.user.natural_key()
    #
    # natural_key.dependencies = ["beach_wood_user.bwuser"]

    class Meta(BaseModelMixin.Meta, StaffMemberMixin.Meta):
        permissions = [
            ("assistant_user", "Assistant User"),
            ("can_access_bookkeeper", _("Can access bookkeeper account details")),
            ("can_edit_bookkeeper", _("Can edit bookkeeper account details")),
            ("can_access_client", _("Can access client(s) account details")),
            ("can_assign_bookkeeper_to_client", _("Assign bookkeeper to client")),
            (
                ASSISTANT_FULL_MANAGER_PERMISSION_SHORT_NAME,
                "Assistant has full manager permissions",
            ),
            ("can_edit_users", "Can edit users"),
        ]
