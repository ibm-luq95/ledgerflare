# -*- coding: utf-8 -*-#
from core.models.managers import SoftDeleteManager
from discussion.models.queryset import DiscussionQuerySet


class RepliesManager(SoftDeleteManager):
    def get_queryset(self) -> DiscussionQuerySet:
        queryset = DiscussionQuerySet(self.model, using=self._db).filter(
            is_deleted=False
        )
        return queryset

    def get_only_discussions_without_replies(self) -> DiscussionQuerySet:
        queryset = self.get_queryset().filter(replies=None)

        return queryset
