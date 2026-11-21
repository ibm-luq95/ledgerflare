# -*- coding: utf-8 -*-#
from core.models.querysets import BaseQuerySetMixin


class DiscussionQuerySet(BaseQuerySetMixin):
    def get_only_discussion(self):
        return self.filter(replies__isnull=True)
