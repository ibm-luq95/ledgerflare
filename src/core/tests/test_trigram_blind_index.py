"""Unit tests for Trigram Blind Indexing core primitives."""

from __future__ import annotations

import pytest
from django.db import models

from core.crypto.blind_index import compute_trigram_blind_index
from core.fields.encrypted_fields import EncryptedCharField


def test_compute_trigram_blind_index_deterministic() -> None:
    """Verify trigram blind indexing produces identical tokens for identical input."""
    trigrams1 = compute_trigram_blind_index(
        "https://qbo.intuit.com/login", context="account:url"
    )
    trigrams2 = compute_trigram_blind_index(
        "https://qbo.intuit.com/login", context="account:url"
    )
    assert isinstance(trigrams1, list)
    assert len(trigrams1) > 0
    assert trigrams1 == trigrams2
    assert all(len(token) == 16 for token in trigrams1)


def test_compute_trigram_blind_index_substring_overlap() -> None:
    """Verify trigram hashes of a substring are a subset of the full string trigram hashes."""
    full_trigrams = compute_trigram_blind_index(
        "chase.com/portal", context="account:url"
    )
    sub_trigrams = compute_trigram_blind_index("chase", context="account:url")
    assert len(sub_trigrams) > 0
    assert set(sub_trigrams).issubset(set(full_trigrams))


def test_compute_trigram_blind_index_short_and_empty() -> None:
    """Verify empty or shorter than 3 chars return empty list."""
    assert compute_trigram_blind_index("") == []
    assert compute_trigram_blind_index(None) == []
    assert compute_trigram_blind_index("ab") == []


class DummyModel(models.Model):
    """Mock model to test trigram blind index pre_save integration."""

    url = EncryptedCharField(max_length=512, trigram_blind_index=True)
    url_bidx = models.JSONField(default=list)

    class Meta:
        """Meta configuration for DummyModel."""

        app_label = "core"

    def __str__(self) -> str:
        """Return string representation."""
        return str(self.url)


def test_encrypted_field_populates_trigram_blind_index() -> None:
    """Verify model field with trigram_blind_index=True populates the bidx field."""
    instance = DummyModel(url="https://wellsfargo.com")
    field = DummyModel._meta.get_field("url")
    field.pre_save(instance, add=True)

    assert isinstance(instance.url_bidx, list)
    assert len(instance.url_bidx) > 0
    assert all(len(token) == 16 for token in instance.url_bidx)
