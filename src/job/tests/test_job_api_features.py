# -*- coding: utf-8 -*-#
from __future__ import annotations

import pytest
from client.views.api import ClientViewSet
from discussion.views.api import DiscussionViewSet
from job.views.api import JobViewSet
from task.views.api import TaskViewSet


@pytest.mark.django_db
def test_core_viewsets_have_filter_search_ordering() -> None:
    for viewset_cls in [JobViewSet, TaskViewSet, ClientViewSet, DiscussionViewSet]:
        assert (
            hasattr(viewset_cls, "filterset_fields")
            and len(viewset_cls.filterset_fields) > 0
        )
        assert (
            hasattr(viewset_cls, "search_fields") and len(viewset_cls.search_fields) > 0
        )
        assert (
            hasattr(viewset_cls, "ordering_fields")
            and len(viewset_cls.ordering_fields) > 0
        )


@pytest.mark.django_db
def test_job_scope_queryset_for_bookkeeper() -> None:
    from django.contrib.auth.models import Group
    from model_bakery import baker
    from beach_wood_user.models import BWUser
    from bookkeeper.models import BookkeeperProxy
    from core.constants.users import (
        BOOKKEEPER_GROUP_NAME,
        ASSISTANT_GROUP_NAME,
        MANAGER_GROUP_NAME,
        CON_BOOKKEEPER,
    )
    from job.models import JobProxy
    from job.views.api import JobViewSet, UpdateJobApiView

    for group_name in [BOOKKEEPER_GROUP_NAME, ASSISTANT_GROUP_NAME, MANAGER_GROUP_NAME]:
        Group.objects.get_or_create(name=group_name)

    user = baker.make(
        BWUser, first_name="Test", last_name="Bookkeeper", user_type=CON_BOOKKEEPER
    )
    bookkeeper = BookkeeperProxy.objects.get(user=user)
    job_viewset = JobViewSet()
    update_view = UpdateJobApiView()

    qs = JobProxy.objects.all()
    # Ensure calling scope_queryset_for_bookkeeper executes valid ORM query without FieldError
    scoped_qs1 = job_viewset.scope_queryset_for_bookkeeper(qs, bookkeeper)
    scoped_qs2 = update_view.scope_queryset_for_bookkeeper(qs, bookkeeper)

    assert scoped_qs1.count() >= 0
    assert scoped_qs2.count() >= 0
