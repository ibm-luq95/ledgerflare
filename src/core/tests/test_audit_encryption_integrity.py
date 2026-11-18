"""Unit tests for audit_encryption_integrity management command."""

from __future__ import annotations

import pytest
from django.core.files.base import ContentFile
from django.core.management import CommandError, call_command

from client_account.models import ClientAccountProxy
from document.models import DocumentProxy


@pytest.mark.django_db
def test_audit_encryption_integrity_detects_violations() -> None:
    """Verify that audit command raises CommandError when unencrypted records or files exist."""
    # Create unencrypted row
    acc = ClientAccountProxy.objects.create(
        account_name="Unencrypted Audit Test",
        account_username="raw_username",
    )
    ClientAccountProxy.objects.filter(pk=acc.pk).update(account_username="raw_username")

    with pytest.raises(CommandError, match="Cryptographic audit failed"):
        call_command("audit_encryption_integrity")


@pytest.mark.django_db
def test_audit_encryption_integrity_passes_when_clean() -> None:
    """Verify that audit command exits cleanly with 0 when all records and files are encrypted."""
    # Empty DB or fully encrypted records
    call_command("audit_encryption_integrity")
