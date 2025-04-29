# -*- coding: utf-8 -*-#
from django.utils import timezone

from cfo.models.cfo import CFO
from cfo.signals.signals import cfo_pre_soft_delete, cfo_post_soft_delete


class CFOProxy(CFO):

    class Meta(CFO.Meta):
        proxy = True

    def delete(self):
        """
        Perform a soft delete and trigger custom signals.
        """
        # Trigger pre_soft_delete signal
        cfo_pre_soft_delete.send(sender=self.__class__, instance=self)

        # Perform soft delete
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

        # Trigger post_soft_delete signal
        cfo_post_soft_delete.send(sender=self.__class__, instance=self)
