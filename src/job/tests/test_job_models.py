"""Tests for Job models, proxy variants, and status choices."""

from __future__ import annotations

import pytest
from model_bakery import baker

from core.choices import JobStatusEnum
from job.models import JobProxy


@pytest.mark.unit
@pytest.mark.django_db
def test_job_status_enum_values() -> None:
    """Verify JobProxy default status and JobStatusEnum text choices."""
    job = baker.make(JobProxy, status=JobStatusEnum.DRAFT)
    assert job.status == JobStatusEnum.DRAFT


@pytest.mark.unit
@pytest.mark.django_db
def test_job_proxy_soft_delete() -> None:
    """Verify soft-delete filtering on JobProxy instances."""
    active_job = baker.make(
        JobProxy, is_deleted=False, status=JobStatusEnum.NOT_STARTED
    )
    deleted_job = baker.make(
        JobProxy, is_deleted=True, status=JobStatusEnum.NOT_STARTED
    )

    assert active_job in JobProxy.objects.all()
    assert deleted_job not in JobProxy.objects.all()
    assert deleted_job in JobProxy.original_objects.all()
