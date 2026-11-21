"""Tests for BaseModelMixin soft-delete manager filtering and restore methods."""

from __future__ import annotations

import pytest
from model_bakery import baker

from client.models import ClientProxy


@pytest.mark.unit
@pytest.mark.django_db
def test_soft_delete_manager_filtering() -> None:
    """Verify objects, original_objects, and archive_objects manager filtering."""
    active_client = baker.make(ClientProxy, name="Active Client", is_deleted=False)
    deleted_client = baker.make(ClientProxy, name="Deleted Client", is_deleted=True)
    archived_client = baker.make(
        ClientProxy, name="Archived Client", status="archived", is_deleted=False
    )

    assert active_client in ClientProxy.objects.all()
    assert deleted_client not in ClientProxy.objects.all()

    assert active_client in ClientProxy.original_objects.all()
    assert deleted_client in ClientProxy.original_objects.all()

    assert archived_client in ClientProxy.archive_objects.all()
    assert active_client not in ClientProxy.archive_objects.all()
    assert deleted_client not in ClientProxy.archive_objects.all()


@pytest.mark.unit
@pytest.mark.django_db
def test_soft_delete_and_restore_methods() -> None:
    """Verify soft delete and restore methods on model instances."""
    client = baker.make(ClientProxy, name="Test Client", is_deleted=False)
    client.delete()

    client.refresh_from_db()
    assert client.is_deleted is True
    assert client.deleted_at is not None

    client.restore()
    client.refresh_from_db()
    assert client.is_deleted is False
    assert client.deleted_at is None
