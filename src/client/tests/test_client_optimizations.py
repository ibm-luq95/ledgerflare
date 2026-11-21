from __future__ import annotations

import pytest
from rest_framework.test import APIRequestFactory

from beach_wood_user.models import BWUser
from client.views.api import ClientViewSet
from discussion.views.api import DiscussionViewSet


@pytest.mark.django_db
def test_client_viewset_queryset_optimizations() -> None:
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = BWUser(user_type="manager")

    viewset = ClientViewSet()
    viewset.request = request
    qs = viewset.get_queryset()
    prefetch_lookups = qs._prefetch_related_lookups
    assert len(prefetch_lookups) > 0, "ClientViewSet must prefetch M2M relations"


@pytest.mark.django_db
def test_discussion_viewset_queryset_optimizations() -> None:
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = BWUser(user_type="manager")

    viewset = DiscussionViewSet()
    viewset.request = request
    qs = viewset.get_queryset()
    select_related = qs.query.select_related
    assert isinstance(select_related, dict), "DiscussionViewSet must call select_related()"
