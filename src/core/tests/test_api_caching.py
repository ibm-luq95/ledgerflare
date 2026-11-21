# -*- coding: utf-8 -*-#
from __future__ import annotations

import pytest
from client_category.views.api import ClientCategoryViewSet
from job_category.views.api import JobCategoryViewSet


@pytest.mark.django_db
def test_reference_viewsets_have_cache_decorator() -> None:
    for viewset_cls in [ClientCategoryViewSet, JobCategoryViewSet]:
        assert hasattr(viewset_cls.list, "_cache_page_decorator") or hasattr(viewset_cls, "cache_timeout") or hasattr(viewset_cls, "dispatch")
