# -*- coding: utf-8 -*-#
from __future__ import annotations

from typing import Type

from discussion.models.discussion import Discussion
from job.models import JobProxy
from special_assignment.models import SpecialAssignmentProxy


class DiscussionProxy(Discussion):
    class Meta(Discussion.Meta):
        proxy = True
        indexes = []

    def for_what(self) -> None | SpecialAssignmentProxy | JobProxy:
        if self.job:
            return self.job
        elif self.special_assignment:
            return self.special_assignment

    def get_absolute_url(self) -> str:
        target = self.for_what()
        if target:
            return target.get_absolute_url()
        return "#"
