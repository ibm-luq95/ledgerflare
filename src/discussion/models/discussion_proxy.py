# -*- coding: utf-8 -*-#
from __future__ import annotations

from typing import Type

from discussion.models.discussion import Discussion
from job.models import JobProxy
from special_assignment.models import SpecialAssignmentProxy


class DiscussionProxy(Discussion):
    class Meta(Discussion.Meta):
        proxy = True

    def for_what(self) -> None | SpecialAssignmentProxy | JobProxy:
        if self.job:
            return self.job
        elif self.special_assignment:
            return self.special_assignment
