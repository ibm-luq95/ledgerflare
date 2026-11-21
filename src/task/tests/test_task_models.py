"""Tests for Task models and proxy variants."""

from __future__ import annotations

import pytest
from model_bakery import baker

from task.models import TaskProxy


@pytest.mark.unit
@pytest.mark.django_db
def test_task_proxy_creation_and_soft_delete() -> None:
    """Verify TaskProxy creation and soft-delete manager isolation."""
    active_task = baker.make(TaskProxy, title="Active Task", is_deleted=False)
    deleted_task = baker.make(TaskProxy, title="Deleted Task", is_deleted=True)

    assert active_task in TaskProxy.objects.all()
    assert deleted_task not in TaskProxy.objects.all()
    assert deleted_task in TaskProxy.original_objects.all()
