from __future__ import annotations

from typing import Any
from itertools import chain

from django.db.models import QuerySet, Model

from beach_wood_user.models import BWUser
from core.utils.developments.debugging_print_object import DebuggingPrint


class LedgerFlareUserUtils:
    def __init__(self, user: BWUser):
        self.user: BWUser = user

    def assigned_special_assignment_notifications(self, is_all: bool = False):
        if is_all is True:
            assigned_notifications = self.user.assigned_notifications.all()  # type: ignore
        else:
            assigned_notifications = self.user.assigned_notifications.filter(  # type: ignore
                is_read=False
            )
        # DebuggingPrint.print(assigned_notifications)
        return assigned_notifications

    def unread_discussions_notifications(
        self, is_all: bool = False
    ) -> QuerySet[Model | Any, Model | Any]:
        if is_all is True:
            discussions_notifications = self.user.discussions_notifications.all()  # type: ignore
        else:
            discussions_notifications = self.user.discussions_notifications.filter(  # type: ignore
                is_read=False
            )
        # DebuggingPrint.pprint(discussions_notifications)
        return discussions_notifications

    def get_all_not_read_notifications(self) -> list[Any]:
        all_notifications = chain(
            self.assigned_special_assignment_notifications(),
            self.unread_discussions_notifications(),
        )
        all_notifications = list(all_notifications)
        all_notifications.sort(key=lambda x: x.created_at, reverse=True)
        return all_notifications

    def get_all_notifications(self) -> list[Any]:
        all_notifications = chain(
            self.assigned_special_assignment_notifications(is_all=True),
            self.unread_discussions_notifications(is_all=True),
        )
        all_notifications = list(all_notifications)
        all_notifications.sort(key=lambda x: x.created_at, reverse=True)
        return all_notifications

    @property
    def get_all_total_not_read_notifications(self) -> int:
        total = (
            self.assigned_special_assignment_notifications().count()
            + self.unread_discussions_notifications().count()
        )
        return total
