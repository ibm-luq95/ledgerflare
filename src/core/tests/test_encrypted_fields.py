from __future__ import annotations

import pytest
from django.db import connection, models

from core.crypto.engine import CryptoEngine
from core.crypto.service import DecryptionIntegrityError
from core.fields.encrypted_fields import EncryptedCharField, EncryptedTextField
from core.models.mixins.base_model import BaseModelMixin
from core.models.mixins.encrypted_model import EncryptedModelMixin


class DummyEncryptedModel(BaseModelMixin, EncryptedModelMixin):
    secret_text = EncryptedTextField(null=True, blank=True)
    secret_char = EncryptedCharField(max_length=255, null=True, blank=True)

    class Meta:
        """Meta options for test model."""

        app_label = "core"
        db_table = "test_core_dummyencryptedmodel"


@pytest.mark.django_db
def test_encrypted_field_db_lifecycle() -> None:
    table_name = DummyEncryptedModel._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")

    with connection.schema_editor() as editor:
        editor.create_model(DummyEncryptedModel)

    try:
        obj = DummyEncryptedModel.objects.create(
            secret_text="Classified Budget Report",
            secret_char="Secret-PIN-9876",
        )
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT secret_text, secret_char FROM {table_name} WHERE id = %s",  # noqa: S608
                [str(obj.pk)],
            )
            raw_row = cursor.fetchone()
            assert raw_row is not None
            assert raw_row[0].startswith("v1:")
            assert raw_row[1].startswith("v1:")
            assert "Classified" not in raw_row[0]

        reloaded = DummyEncryptedModel.objects.get(pk=obj.pk)
        assert reloaded.secret_text == "Classified Budget Report"
        assert reloaded.secret_char == "Secret-PIN-9876"
        assert reloaded.verify_record_integrity() is True
    finally:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")


@pytest.mark.django_db
def test_encrypted_field_none_and_empty_handling() -> None:
    table_name = DummyEncryptedModel._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")

    with connection.schema_editor() as editor:
        editor.create_model(DummyEncryptedModel)

    try:
        obj = DummyEncryptedModel.objects.create(secret_text=None, secret_char="")
        reloaded = DummyEncryptedModel.objects.get(pk=obj.pk)
        assert reloaded.secret_text is None
        assert reloaded.secret_char == ""
        assert reloaded.verify_record_integrity() is True
    finally:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")


@pytest.mark.django_db
def test_encrypted_field_update_lifecycle() -> None:
    table_name = DummyEncryptedModel._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")

    with connection.schema_editor() as editor:
        editor.create_model(DummyEncryptedModel)

    try:
        obj = DummyEncryptedModel.objects.create(secret_text="Initial Text")
        assert obj.secret_text == "Initial Text"

        obj.secret_text = "Updated Text Value"
        obj.save()

        reloaded = DummyEncryptedModel.objects.get(pk=obj.pk)
        assert reloaded.secret_text == "Updated Text Value"
        assert reloaded.verify_record_integrity() is True
    finally:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")


@pytest.mark.django_db
def test_tampered_ciphertext_detection() -> None:
    table_name = DummyEncryptedModel._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")

    with connection.schema_editor() as editor:
        editor.create_model(DummyEncryptedModel)

    try:
        obj = DummyEncryptedModel.objects.create(secret_text="Genuine Record")
        # Tamper ciphertext in database
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE {table_name} SET secret_text = %s WHERE id = %s",  # noqa: S608
                ["v1:k1:tampered:ciphertext:tag", str(obj.pk)],
            )

        reloaded = DummyEncryptedModel.objects.get(pk=obj.pk)
        assert reloaded.verify_record_integrity() is False

        with pytest.raises(DecryptionIntegrityError):
            _ = reloaded.secret_text
    finally:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")


@pytest.mark.django_db
def test_cross_record_transplant_detection() -> None:
    table_name = DummyEncryptedModel._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")

    with connection.schema_editor() as editor:
        editor.create_model(DummyEncryptedModel)

    try:
        rec_a = DummyEncryptedModel.objects.create(secret_text="Record A Secret")
        rec_b = DummyEncryptedModel.objects.create(secret_text="Record B Secret")

        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT secret_text FROM {table_name} WHERE id = %s",  # noqa: S608
                [str(rec_a.pk)],
            )
            cipher_a = cursor.fetchone()[0]

            # Transplant Record A's ciphertext into Record B
            cursor.execute(
                f"UPDATE {table_name} SET secret_text = %s WHERE id = %s",  # noqa: S608
                [cipher_a, str(rec_b.pk)],
            )

        reloaded_b = DummyEncryptedModel.objects.get(pk=rec_b.pk)
        assert reloaded_b.verify_record_integrity() is False

        with pytest.raises(DecryptionIntegrityError):
            _ = reloaded_b.secret_text
    finally:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")


@pytest.mark.django_db
def test_legacy_fernet_descriptor_access() -> None:
    table_name = DummyEncryptedModel._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")

    with connection.schema_editor() as editor:
        editor.create_model(DummyEncryptedModel)

    try:
        obj = DummyEncryptedModel.objects.create()
        fernet_token = CryptoEngine.encrypt("legacy_password_xyz")

        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE {table_name} SET secret_char = %s WHERE id = %s",  # noqa: S608
                [fernet_token, str(obj.pk)],
            )

        reloaded = DummyEncryptedModel.objects.get(pk=obj.pk)
        assert reloaded.secret_char == "legacy_password_xyz"
        assert reloaded.verify_record_integrity() is True
    finally:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")


class DummySearchableModel(BaseModelMixin, EncryptedModelMixin):
    secret_account = EncryptedCharField(
        max_length=255, blind_index=True, null=True, blank=True
    )
    secret_account_bidx = models.CharField(
        max_length=64, db_index=True, default="", blank=True
    )

    class Meta:
        """Meta options for searchable test model."""

        app_label = "core"
        db_table = "test_core_dummysearchablemodel"


@pytest.mark.django_db
def test_blind_index_generation_and_exact_query() -> None:
    table_name = DummySearchableModel._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")

    with connection.schema_editor() as editor:
        editor.create_model(DummySearchableModel)

    try:
        rec1 = DummySearchableModel.objects.create(secret_account="ACC-1234-5678-ABCD")
        rec2 = DummySearchableModel.objects.create(secret_account="ACC-9999-8888-ZZZZ")

        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT secret_account, secret_account_bidx FROM {table_name} WHERE id = %s",  # noqa: S608
                [str(rec1.pk)],
            )
            raw_cipher, raw_bidx = cursor.fetchone()
            assert raw_cipher.startswith("v1:k1:")
            assert len(raw_bidx) == 64
            assert "ACC-1234" not in raw_cipher
            assert "ACC-1234" not in raw_bidx

        query = DummySearchableModel.get_blind_index_query(
            "secret_account", "acc-1234-5678-abcd"
        )
        results = list(DummySearchableModel.objects.filter(**query))
        assert len(results) == 1
        assert results[0].pk == rec1.pk
        assert results[0].secret_account == "ACC-1234-5678-ABCD"

        query_rec2 = DummySearchableModel.get_blind_index_query(
            "secret_account", "ACC-9999-8888-ZZZZ"
        )
        results_rec2 = list(DummySearchableModel.objects.filter(**query_rec2))
        assert len(results_rec2) == 1
        assert results_rec2[0].pk == rec2.pk

        unknown_query = DummySearchableModel.get_blind_index_query(
            "secret_account", "UNKNOWN-ACCT"
        )
        assert DummySearchableModel.objects.filter(**unknown_query).count() == 0

        rec1.secret_account = "ACC-MODIFIED-0000"
        rec1.save()
        reloaded1 = DummySearchableModel.objects.get(pk=rec1.pk)
        assert reloaded1.secret_account == "ACC-MODIFIED-0000"

        mod_query = DummySearchableModel.get_blind_index_query(
            "secret_account", "acc-modified-0000"
        )
        assert DummySearchableModel.objects.filter(**mod_query).first().pk == rec1.pk
    finally:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
