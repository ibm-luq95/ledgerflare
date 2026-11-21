# -*- coding: utf-8 -*-#
from django.db import transaction

from core.constants.status_labels import CON_COMPLETED
from task.models import Task


class TaskProxy(Task):
    """A proxy model representing a Task in the system.

    This class extends the Task model and provides additional methods and functionality.

    Attributes:
        Meta (class): Contains the proxy configuration for the TaskProxy model.

    Methods:
        get_is_completed_label(self) -> str: Returns the label for the task completion status.
        save(self, *args, **kwargs): Sets the 'is_completed' attribute based on the task status.
        get_client(): Returns the client associated with the task's job, if available.
        log_task_to_history(self) -> None: Logs the task to the task history. (Currently not implemented)
        unlog_task_from_history(self) -> None: Unlogs the task from the task history. (Currently not implemented)
    """

    class Meta(Task.Meta):
        proxy = True
        indexes = []

    def get_is_completed_label(self) -> str:
        if self.is_completed is True:
            return "Completed"
        else:
            return "Not completed"

    def save(self, *args, **kwargs):
        if self.status == CON_COMPLETED:
            self.is_completed = True
        else:
            self.is_completed = False
        super().save(*args, **kwargs)

    def get_client(self):
        if hasattr(self, "job"):
            if hasattr(self.job, "client"):
                return self.job.client
            else:
                return None
        return None

    # def log_task_to_history(self) -> None:
    #     with transaction.atomic():
    #         from . import TaskHistory
    #
    #         history_obj, created = TaskHistory.objects.get_or_create(
    #             task=self,
    #             defaults={
    #                 "task": self,
    #                 "previous_status": self.status,
    #                 "is_archived": True,
    #             },
    #         )
    #
    # def unlog_task_from_history(self) -> None:
    #     pass
