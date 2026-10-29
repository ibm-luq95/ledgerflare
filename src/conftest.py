from __future__ import annotations

from typing import Any, Callable

import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker
from rest_framework.test import APIClient

baker.generators.add(
    "core.fields.encrypted_fields.EncryptedTextField",
    lambda: "Sample encrypted text",
)
baker.generators.add(
    "core.fields.encrypted_fields.EncryptedCharField",
    lambda: "Sample encrypted char",
)

User = get_user_model()


@pytest.fixture
def admin_user(db: Any) -> Any:
    return baker.make(
        User, is_superuser=True, is_staff=True, email="admin@ledgerflare.com"
    )


@pytest.fixture
def manager_user(db: Any) -> Any:
    user = baker.make(User, is_staff=True, email="manager@ledgerflare.com")
    user.groups.create(name="Manager")
    return user


@pytest.fixture
def bookkeeper_user(db: Any) -> Any:
    user = baker.make(User, is_staff=True, email="bookkeeper@ledgerflare.com")
    user.groups.create(name="Bookkeeper")
    return user


@pytest.fixture
def assistant_user(db: Any) -> Any:
    user = baker.make(User, is_staff=True, email="assistant@ledgerflare.com")
    user.groups.create(name="Assistant")
    return user


@pytest.fixture
def cfo_user(db: Any) -> Any:
    user = baker.make(User, is_staff=True, email="cfo@ledgerflare.com")
    user.groups.create(name="CFO")
    return user


@pytest.fixture
def client_user(db: Any) -> Any:
    return baker.make(User, is_staff=False, email="client@external.com")


@pytest.fixture
def anon_api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def auth_api_client() -> Callable[[Any], APIClient]:
    def _client(user: Any) -> APIClient:
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    return _client
