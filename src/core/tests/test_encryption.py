"""Tests for encrypted credential storage vs raw database values."""

from __future__ import annotations

import pytest
from django.db import connection
from model_bakery import baker

from client_account.models import ClientAccountProxy


@pytest.mark.security
@pytest.mark.django_db
def test_client_account_password_encryption() -> None:
    """Verify account_password is stored encrypted in database."""
    secret_pass = "SuperSecretPass123!"
    account = baker.make(ClientAccountProxy, account_password=secret_pass)

    assert account.decrypted_account_password == secret_pass

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT account_password FROM client_account_clientaccount WHERE id = %s",
            [str(account.id)],
        )
        raw_val = cursor.fetchone()[0]
        assert secret_pass not in raw_val
