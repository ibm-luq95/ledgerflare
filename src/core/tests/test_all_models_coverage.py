"""Comprehensive model lifecycle and soft-delete tests across proxy variants."""

from __future__ import annotations

import pytest
from model_bakery import baker

from client.models import ClientProxy
from fiscal_year.models import FiscalYear
from job.models import JobProxy
from task.models import TaskProxy


@pytest.mark.unit
@pytest.mark.django_db
def test_all_proxy_models_soft_delete_lifecycle() -> None:
    """Verify soft-delete lifecycle across core domain proxy models."""
    client = baker.make(ClientProxy, name="Test Client", is_deleted=False)
    client.delete()
    client.refresh_from_db()
    assert client.is_deleted is True
    assert client.deleted_at is not None

    job = baker.make(JobProxy, title="Test Job", is_deleted=False)
    job.delete()
    job.refresh_from_db()
    assert job.is_deleted is True
    assert job.deleted_at is not None

    task = baker.make(TaskProxy, title="Test Task", is_deleted=False)
    task.delete()
    task.refresh_from_db()
    assert task.is_deleted is True
    assert task.deleted_at is not None


@pytest.mark.unit
@pytest.mark.django_db
def test_fiscal_year_active_state() -> None:
    """Verify FiscalYear model attributes."""
    fy = baker.make(FiscalYear, year=2026, is_current_active=True)
    assert fy.is_current_active is True
    assert fy.year == 2026
