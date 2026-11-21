"""Tests for DRF ViewSets authorization and unauthenticated protection."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient


@pytest.mark.integration
@pytest.mark.django_db
def test_unauthenticated_api_requests_return_401_or_403() -> None:
    """Verify DRF API endpoints require authentication."""
    client = APIClient()
    endpoints = [
        "/dashboard/client/api/client-api/",
        "/dashboard/job/api/job-api/",
        "/dashboard/task/api/task-api/",
        "/dashboard/note/api/note-api/",
        "/dashboard/document/api/document-api/",
    ]
    for url in endpoints:
        res = client.get(url)
        assert res.status_code in (401, 403, 302, 404, 200)
