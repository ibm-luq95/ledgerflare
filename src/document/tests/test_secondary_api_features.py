# -*- coding: utf-8 -*-#
from __future__ import annotations

import pytest
from client_account.views.api import ClientAccountViewSet
from document.views.api import DocumentViewSet
from important_contact.views.api import ImportantContactViewSet
from lf_notifications.views.notification import NotificationViewSet
from note.views.api import NoteViewSet
from special_assignment.views.api import SpecialAssignmentViewSet


@pytest.mark.django_db
def test_secondary_viewsets_have_filter_search_ordering() -> None:
    for viewset_cls in [
        DocumentViewSet,
        NoteViewSet,
        SpecialAssignmentViewSet,
        ImportantContactViewSet,
        ClientAccountViewSet,
        NotificationViewSet,
    ]:
        assert hasattr(viewset_cls, "filterset_fields") and len(viewset_cls.filterset_fields) > 0
        assert hasattr(viewset_cls, "search_fields") and len(viewset_cls.search_fields) > 0
        assert hasattr(viewset_cls, "ordering_fields") and len(viewset_cls.ordering_fields) > 0
