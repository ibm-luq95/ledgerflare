# -*- coding: utf-8 -*-#
from django.utils import timezone

from manager.models import Manager
from manager.signals.signals import (
    manager_pre_soft_delete,
    manager_post_soft_delete,
)


class ManagerProxy(Manager):
    class Meta(Manager.Meta):
        proxy = True

    def delete(self):
        """
        Perform a soft delete and trigger custom signals.
        """
        # Trigger pre_soft_delete signal
        manager_pre_soft_delete.send(sender=self.__class__, instance=self)

        # Perform soft delete
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

        # Trigger post_soft_delete signal
        manager_post_soft_delete.send(sender=self.__class__, instance=self)
