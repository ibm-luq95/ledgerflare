# -*- coding: utf-8 -*-#
import traceback
from typing import Optional

from core.constants.status_labels import (
    CON_PAST_DUE,
    CON_STALLED,
    CON_NEED_INFO,
    CON_ARCHIVED,
    CON_COMPLETED,
)
from core.models.querysets import BaseQuerySetMixin
from bookkeeper.models import Bookkeeper
from core.utils import BeachWoodFinancialError, get_formatted_logger, debugging_print
from django.db.models import Q

from core.utils.developments.debugging_print_object import DebuggingPrint


logger = get_formatted_logger()


class BookkeeperProxy(Bookkeeper):
    """BookkeeperProxy model

    Represents a proxy model for the Bookkeeper model.
    Inherits from the Bookkeeper model and serves as a proxy for accessing and extending its functionality.
    """

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

    class Meta(Bookkeeper.Meta):
        proxy = True

    @property
    def get_bookkeeper(self) -> Bookkeeper:
        return Bookkeeper.objects.get(pk=self.pk)

    def get_tasks_count(self):
        all_tasks = []
        all_jobs = self.user.jobs.all()
        if all_jobs:
            for job in all_jobs:
                all_tasks.append(job.tasks.count())
        return sum(all_tasks)

    # def get_all_tasks_qs(self) -> BaseQuerySetMixin | None:
    #     from task.models import TaskProxy
    #
    #     bookkeeper_jobs = self.get_user_jobs()
    #     debugging_print(bookkeeper_jobs)
    #     if bookkeeper_jobs:
    #         all_tasks_list = []
    #         for job in bookkeeper_jobs:
    #             tasks = job.tasks.all()
    #             if tasks:
    #                 all_tasks_list = all_tasks_list + [task.pk for task in tasks]
    #         all_tasks_qs = TaskProxy.objects.filter(pk__in=all_tasks_list)
    #         return all_tasks_qs
    #     else:
    #         return None

    @property
    def get_clients_total(self) -> int:
        total_list = set()
        jobs = self.jobs.all()
        if jobs:
            for job in jobs:
                total_list.add(str(job.client.pk))
        return len(total_list)

    def get_tasks(self) -> list:
        all_lists = []
        all_jobs = self.user.jobs.all()
        if all_jobs:
            for job in all_jobs:
                tasks = job.tasks.all()
                if tasks:
                    for task in tasks:
                        all_lists.append(task)
        return all_lists

    def get_all_jobs(self):
        from job.models import JobProxy

        all_jobs = JobProxy.original_objects.filter(managed_by=self.user)
        return all_jobs

    def get_user_jobs(self, is_archived: bool = False) -> BaseQuerySetMixin | None:
        if hasattr(self.user, "jobs"):
            if is_archived is True:
                return self.user.jobs.filter(status__in=[CON_ARCHIVED, CON_COMPLETED])
            else:
                return self.user.jobs.all()
        else:
            return None

    def get_past_due_jobs(self) -> BaseQuerySetMixin | None:
        if hasattr(self.user, "jobs"):
            return self.user.jobs.filter(status=CON_PAST_DUE)
        else:
            return None

    def get_stats_jobs(self) -> BaseQuerySetMixin | None:
        if hasattr(self.user, "jobs"):
            return self.user.jobs.filter(Q(state=CON_STALLED) | Q(state=CON_NEED_INFO))
        else:
            return None

    def get_all_related_items(
        self, custom_item_name: Optional[str] = None, is_archived: bool = False
    ) -> dict | list:
        from job.models.job_proxy import JobProxy
        from note.models import Note
        from task.models.proxy_model import TaskProxy
        from document.models.document import Document

        items_dict = dict()
        items_dict["tasks"] = []
        items_dict["documents"] = []
        items_dict["notes"] = []
        items_dict["jobs"] = []
        documents = []
        notes_list = []
        # get tasks from jobs
        jobs = self.get_user_jobs()
        if jobs:
            jobs_pks = [job.pk for job in jobs]
            items_dict["jobs"] = JobProxy.objects.filter(pk__in=jobs_pks)
            for job in jobs:
                tasks = job.tasks.all()
                if tasks:
                    items_dict["tasks"] = tasks
                    for task in tasks:
                        docs = task.documents.all()
                        if docs:
                            # documents += [doc for doc in docs]
                            documents += docs
                            items_dict["documents"] = documents

                        notes = task.notes.all()
                        if notes:
                            # notes_list += [note for note in notes]
                            notes_list += notes
                            items_dict["notes"] = notes_list
                job_documents = job.documents.all()
                if job_documents:
                    documents += job_documents
                    items_dict["documents"] = documents

        clients = self.clients.all()
        if clients:
            for client in clients:
                notes = client.notes.all()
                if notes:
                    items_dict["notes"] += notes
                documents = client.documents.all()
                if documents:
                    items_dict["documents"] += documents
        if items_dict["notes"]:
            notes_pks = [note.pk for note in items_dict["notes"]]
            items_dict["notes"] = Note.objects.filter(pk__in=notes_pks)
        else:
            items_dict["notes"] = Note.objects.none()
        if items_dict["tasks"]:
            tasks_pks = [task.pk for task in items_dict["tasks"]]
            items_dict["tasks"] = TaskProxy.objects.filter(pk__in=tasks_pks)
        else:
            items_dict["tasks"] = TaskProxy.objects.none()
        if items_dict["documents"]:
            documents_pks = [doc.pk for doc in items_dict["documents"]]
            items_dict["documents"] = Document.objects.filter(pk__in=documents_pks)
        else:
            items_dict["documents"] = Document.objects.none()
        if custom_item_name is not None:
            return items_dict.get(custom_item_name)
        else:
            return items_dict

    def get_last_tasks(self, task_limit: int = 5) -> list:
        """Retrieve last tasks for bookkeeper

        Args:
            self: bookkeeper instance
            task_limit: int limit of last tasks
        Raises:
            ProjectError: If any exception occurred
            Exception: Any exception will occur will return None

        Returns:
            list: List of last tasks
            None: If any exception occurred
        """
        try:
            tasks_list = []
            all_jobs = self.get_user_jobs()
            all_jobs = all_jobs[:task_limit]
            if all_jobs:
                for job in all_jobs:
                    # debugging_print(job.title)
                    if job.tasks.filter():
                        for task in job.tasks.filter():
                            if len(tasks_list) <= task_limit:
                                tasks_list.append(task)
            # print(len(tasks_list))
            # print(type(tasks_list))
            return tasks_list
        except BeachWoodFinancialError as ex:
            logger.error(traceback.format_exc())
            raise Exception(ex.message)
        except Exception as ex:
            logger.error(traceback.format_exc())
            raise Exception(str(ex))
