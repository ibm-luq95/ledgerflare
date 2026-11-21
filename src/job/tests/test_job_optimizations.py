# -*- coding: utf-8 -*-#
from __future__ import annotations

import pytest
from rest_framework.test import APIRequestFactory

from beach_wood_user.models import BWUser
from job.views.api import JobViewSet
from task.views.api import TaskViewSet


@pytest.mark.django_db
def test_job_viewset_queryset_optimizations() -> None:
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = BWUser(user_type="manager")

    viewset = JobViewSet()
    viewset.request = request
    qs = viewset.get_queryset()
    select_related = qs.query.select_related
    assert isinstance(select_related, dict), "JobViewSet must call select_related()"
    assert "client" in select_related or "managed_by" in select_related


@pytest.mark.django_db
def test_task_viewset_queryset_optimizations() -> None:
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = BWUser(user_type="manager")

    viewset = TaskViewSet()
    viewset.request = request
    qs = viewset.get_queryset()
    select_related = qs.query.select_related
    assert isinstance(select_related, dict), "TaskViewSet must call select_related()"
    assert "job" in select_related
