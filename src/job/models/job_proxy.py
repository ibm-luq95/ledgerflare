# -*- coding: utf-8 -*-#
from django.db import transaction
from django.db.models import Q, Manager

from bookkeeper.models import BookkeeperProxy
from core.constants.status_labels import (
    CON_ARCHIVED,
    CON_COMPLETED,
    CON_ENABLED,
    CON_NOT_STARTED,
)
from job.models import Job


class JobProxy(Job):
    """
    A proxy model representing a Job in the system.

    This class extends the Job model and provides additional methods like 'unplug_bookkeeper_for_client_finished_job'
    to handle operations related to managing bookkeepers for finished jobs.

    Attributes:
        Managed Fields:
            - managed_by: The user who manages the job.
            - status: The status of the job (e.g., CON_COMPLETED, CON_ARCHIVED).
            - client: The client associated with the job.

    Methods:
        unplug_bookkeeper_for_client_finished_job(self):
            Method to unplug the bookkeeper for a finished job. It removes the bookkeeper associated with the job's manager
            from the client's bookkeeper list.

    """

    # objects = Manager()  # This only enable when import using django-import-export package

    class Meta(Job.Meta):
        proxy = True

    def unplug_bookkeeper_for_client_finished_job(self):
        managed_by = self.managed_by
        if self.status == CON_COMPLETED or self.status == CON_ARCHIVED:
            if managed_by:
                with transaction.atomic():
                    client = self.client
                    if hasattr(managed_by, "bookkeeper"):
                        bookkeeper_obj = managed_by.bookkeeper
                        bookkeeper_obj = BookkeeperProxy.objects.get(pk=bookkeeper_obj.pk)
                        client.bookkeepers.remove(bookkeeper_obj)
                        client.save()
                        JobProxy.objects.filter(pk=self.pk).update(managed_by=None)
