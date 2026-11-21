from __future__ import annotations

import io
from datetime import UTC, datetime, timedelta, timezone

import pytest
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import mail
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import RequestFactory

from core.crypto.service import DecryptionIntegrityError, EncryptionService
from core.middleware.session_timeout import SessionInactivityTimeoutMiddleware
from core.services.alert_dispatcher import send_urgent_security_alert
from core.storage.encrypted_storage import EncryptedPrivateStorage


@pytest.mark.unit
def test_fidelity_multilingual_roundtrip() -> None:
    aad = b"Task:additional_notes:123e4567-e89b-12d3-a456-426614174000"
    test_strings = [
        "ASCII only text with numbers 1234567890",
        "Unicode with accents: Café, Noël, façade, José, naïve",
        "اللغة العربية: تفاصيل مالية سرية ومعلومات العميل وحساباته البنكية",
        "Emojis and symbols: 💰 🔒 📈 €150,000.50 & ¥20,000,000",
    ]
    for text in test_strings:
        encrypted = EncryptionService.encrypt(text, aad)
        decrypted = EncryptionService.decrypt(encrypted, aad)
        assert decrypted == text


@pytest.mark.unit
def test_fidelity_binary_documents(tmp_path: pytest.TempPathFactory) -> None:
    storage = EncryptedPrivateStorage(location=str(tmp_path))
    # Simulated password-protected PDF bytes
    pdf_bytes = (
        b"%PDF-1.7\r\n\x00\xff\xfe\xfd/Encrypt 12 0 R /Filter /Standard /V 5 /R 6 /Length 256"
        + b"\xca\xfe\xba\xbe" * 500
    )
    saved_name = storage.save("protected_document.pdf", ContentFile(pdf_bytes))

    with storage.open(saved_name, "rb") as f:
        read_bytes = f.read()

    assert read_bytes == pdf_bytes


@pytest.mark.unit
def test_tamper_detection_bit_flip() -> None:
    aad = b"Task:hints:123e4567-e89b-12d3-a456-426614174000"
    encrypted = EncryptionService.encrypt("Top Secret Hint", aad)
    parts = encrypted.split(":")
    corrupted_tag = parts[4][:-1] + ("A" if parts[4][-1] != "A" else "B")
    tampered_envelope = f"{parts[0]}:{parts[1]}:{parts[2]}:{parts[3]}:{corrupted_tag}"

    with pytest.raises(DecryptionIntegrityError):
        EncryptionService.decrypt(tampered_envelope, aad)


@pytest.mark.unit
def test_aad_anti_transplant_attack() -> None:
    aad_client1 = b"Task:additional_notes:11111111-1111-1111-1111-111111111111"
    aad_client2 = b"Task:additional_notes:22222222-2222-2222-2222-222222222222"

    secret_note = "Account balance: $500,000"
    encrypted = EncryptionService.encrypt(secret_note, aad_client1)

    # Decrypting with legitimate key but different row PK must fail
    with pytest.raises(DecryptionIntegrityError):
        EncryptionService.decrypt(encrypted, aad_client2)


@pytest.mark.django_db
def test_session_inactivity_boundary() -> None:
    rf = RequestFactory()
    user = get_user_model().objects.create_user(
        email="session_test@ledgerflare.com", password="password"
    )

    now = datetime.now(UTC)
    middleware = SessionInactivityTimeoutMiddleware(lambda r: None)

    # 1. Active request at 29 minutes (1740s) must NOT expire
    req_active = rf.get("/dashboard/")
    req_active.user = user
    SessionMiddleware(lambda r: None).process_request(req_active)
    req_active.session["last_activity"] = (now - timedelta(minutes=29)).isoformat()
    resp_active = middleware(req_active)
    assert resp_active is None or resp_active.status_code != 302
    assert datetime.fromisoformat(req_active.session["last_activity"]) >= now

    # 2. Inactive request at 31 minutes (1860s) MUST expire and redirect
    req_expired = rf.get("/dashboard/")
    req_expired.user = user
    SessionMiddleware(lambda r: None).process_request(req_expired)
    req_expired.session["last_activity"] = (now - timedelta(minutes=31)).isoformat()
    resp_expired = middleware(req_expired)
    assert resp_expired is not None
    assert resp_expired.status_code == 302
    assert "reason=timeout" in resp_expired.url


@pytest.mark.unit
def test_alert_cooldown_anti_flood() -> None:
    from django.core.cache import cache

    cache.clear()
    mail.outbox.clear()
    for _ in range(5):
        send_urgent_security_alert(
            category="TAMPER_ATTACK",
            title="Ciphertext bit flip detected",
            details={"ip": "192.168.1.100"},
        )
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_migration_dry_run_idempotency() -> None:
    out = io.StringIO()
    call_command("migrate_encryption", "--dry-run", stdout=out)
    call_command("migrate_encryption", "--dry-run", stdout=out)
    output = out.getvalue()
    assert "DRY RUN COMPLETE" in output
    assert "Database mutations: 0" in output
