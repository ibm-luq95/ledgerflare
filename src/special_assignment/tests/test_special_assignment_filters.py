# -*- coding: utf-8 -*-#
from __future__ import annotations

from datetime import timedelta
import pytest
from django.utils import timezone
from model_bakery import baker

from core.choices.special_assignment import SpecialAssignmentStatusEnum
from special_assignment.filters.special_assignment import SpecialAssignmentFilter
from special_assignment.models import SpecialAssignmentProxy


@pytest.mark.django_db
def test_special_assignment_filter_by_status_and_title():
    sa1 = baker.make(
        SpecialAssignmentProxy,
        title="Audit Tax Return",
        status=SpecialAssignmentStatusEnum.IN_PROGRESS,
    )
    baker.make(
        SpecialAssignmentProxy,
        title="Prepare Balance Sheet",
        status=SpecialAssignmentStatusEnum.COMPLETED,
    )

    filter_status = SpecialAssignmentFilter(
        {"status": SpecialAssignmentStatusEnum.IN_PROGRESS},
        queryset=SpecialAssignmentProxy.objects.all(),
    )
    assert filter_status.qs.count() == 1
    assert filter_status.qs.first().pk == sa1.pk

    filter_title = SpecialAssignmentFilter(
        {"title": "Audit"},
        queryset=SpecialAssignmentProxy.objects.all(),
    )
    assert filter_title.qs.count() == 1
    assert filter_title.qs.first().pk == sa1.pk


@pytest.mark.django_db
def test_special_assignment_filter_by_due_date_range():
    today = timezone.now().date()
    baker.make(
        SpecialAssignmentProxy,
        title="Past Assignment",
        due_date=today - timedelta(days=5),
    )
    sa_future = baker.make(
        SpecialAssignmentProxy,
        title="Future Assignment",
        due_date=today + timedelta(days=5),
    )

    filter_due = SpecialAssignmentFilter(
        {
            "due_date_after": (today - timedelta(days=1)).isoformat(),
            "due_date_before": (today + timedelta(days=10)).isoformat(),
        },
        queryset=SpecialAssignmentProxy.objects.all(),
    )

    assert filter_due.qs.count() == 1
    assert filter_due.qs.first().pk == sa_future.pk
