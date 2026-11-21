# -*- coding: utf-8 -*-#
from django.db import transaction
from django.db.models import Q

from core.constants.status_labels import CON_ARCHIVED
from core.constants.status_labels import CON_COMPLETED
from core.constants.status_labels import CON_ENABLED
from core.models.querysets import BaseQuerySetMixin
from core.utils import get_formatted_logger
from core.utils.developments.debugging_print_object import DebuggingPrint
from job.models import Job
from job.models import JobProxy

logger = get_formatted_logger("bw_error_logger")


class JobArchiveRelatedItemsHelper:
    def __init__(self, job_object: Job | JobProxy):
        self.job_object = job_object

        self.run_helper()

    def run_helper(self) -> None:
        """
        A function that runs a series of database transactions to update the status of
        notes and documents based on the job status.
        """
        try:
            with transaction.atomic():
                status = self.job_object.status
                notes: BaseQuerySetMixin = self.job_object.notes(
                    manager="original_objects"
                ).all()
                documents: BaseQuerySetMixin = self.job_object.documents(
                    manager="original_objects"
                ).all()

                if status == CON_ARCHIVED or status == CON_COMPLETED:
                    if notes:
                        notes.update(status=CON_ARCHIVED)
                    if documents:
                        documents.update(status=CON_ARCHIVED)
                else:
                    if notes:
                        notes.filter(Q(status=CON_ARCHIVED)).update(status=CON_ENABLED)
                    if documents:
                        documents.filter(Q(status=CON_ARCHIVED)).update(
                            status=CON_ENABLED
                        )
        except Exception as ex:
            logger.error(ex)
            DebuggingPrint.print_exception()
