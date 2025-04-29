# -*- coding: utf-8 -*-#
from __future__ import annotations

from django.db import transaction
from django.db.models import Q, Manager
from django.urls import reverse_lazy

from beach_wood_user.models import BWUser
from bookkeeper.models import BookkeeperProxy
from core.constants.status_labels import (
    CON_ARCHIVED,
    CON_COMPLETED,
    CON_ENABLED,
    CON_NOT_STARTED,
)
from core.utils.developments.debugging_print_object import DebuggingPrint
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

    def get_absolute_url(self):
        return reverse_lazy("dashboard:job:details", kwargs={"pk": self.pk})

    def get_staff_discussions(self) -> list[BWUser] | None:
        users: list[BWUser] = []
        if hasattr(self, "discussions"):
            discussions = set(self.discussions.all())
            for d in discussions:
                # DebuggingPrint.pprint(d.get_user_type)
                # DebuggingPrint.pprint(d.get_managed_user())
                users.append(d.get_managed_user().user)
            users: list[BWUser] = list(set(users))
            return users
        else:
            return None
        # DebuggingPrint.pprint(discussions)

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
