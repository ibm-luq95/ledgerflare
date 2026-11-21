# -*- coding: utf-8 -*-#
from __future__ import annotations

import pytest
from client_category.views.api import ClientCategoryViewSet
from job_category.views.api import JobCategoryViewSet
from staff_briefcase.views.accounts.api import StaffAccountsViewSet
from staff_briefcase.views.documents.api import StaffDocumentsViewSet
from staff_briefcase.views.notes.api import StaffNotesViewSet


@pytest.mark.django_db
def test_reference_viewsets_have_filter_search_ordering() -> None:
    for viewset_cls in [
        ClientCategoryViewSet,
        JobCategoryViewSet,
        StaffAccountsViewSet,
        StaffDocumentsViewSet,
        StaffNotesViewSet,
    ]:
        assert hasattr(viewset_cls, "filterset_fields") and len(viewset_cls.filterset_fields) > 0
        assert hasattr(viewset_cls, "search_fields") and len(viewset_cls.search_fields) > 0
        assert hasattr(viewset_cls, "ordering_fields") and len(viewset_cls.ordering_fields) > 0
