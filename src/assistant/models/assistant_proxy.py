# -*- coding: utf-8 -*-#
from django.utils import timezone

from core.constants.users import (
    ASSISTANT_FULL_MANAGER_PERMISSION_WITH_MODEL_NAME,
)
from assistant.models import Assistant
from assistant.signals.signals import (
    assistant_pre_soft_delete,
    assistant_post_soft_delete,
)


class AssistantProxy(Assistant):
    """A proxy model for the Assistant model.

    This class acts as a proxy model for the Assistant model, allowing additional methods
    or behaviors to be defined without modifying the original Assistant model.

    Attributes:
        Inherits all attributes and behavior from the Assistant model.

    Methods:
        is_has_manager_permissions(self) -> bool:
            A method that checks if the assistant has full manager permissions.
            Returns True if the assistant has the full manager permissions, False otherwise.

    Meta:
        Contains metadata for the AssistantProxy class.
        proxy = True indicates that this is a proxy model.
    """

    class Meta(Assistant.Meta):
        proxy = True

    def delete(self):
        """
        Perform a soft delete and trigger custom signals.
        """
        # Trigger pre_soft_delete signal
        assistant_pre_soft_delete.send(sender=self.__class__, instance=self)

        # Perform soft delete
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

        # Trigger post_soft_delete signal
        assistant_post_soft_delete.send(sender=self.__class__, instance=self)

    def is_has_manager_permissions(self) -> bool:
        """Check if the assistant has full manager permissions.

        Returns:
            bool: True if the assistant has full manager permissions, False otherwise.
        """
        return self.user.has_perm(ASSISTANT_FULL_MANAGER_PERMISSION_WITH_MODEL_NAME)
