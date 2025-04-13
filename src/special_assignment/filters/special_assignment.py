# -*- coding: utf-8 -*-#
from core.filters.filter_created_mixin import FilterCreatedMixin
from special_assignment.models import SpecialAssignmentProxy


class SpecialAssignmentFilter(FilterCreatedMixin):
    class Meta:
        model = SpecialAssignmentProxy
        fields = {
            "assigned_by": ["exact"],
            "assigned_to": ["exact"],
            "title": ["icontains"],
            "client": ["exact"],
            "job": ["exact"],
            "status": ["exact"],
            "is_seen": ["exact"],
        }
