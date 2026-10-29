from __future__ import annotations

import json
from pathlib import Path

import pytest
from django.core import mail

from core.logging.security_logger import log_security_event
from core.services.alert_dispatcher import send_urgent_security_alert


@pytest.mark.unit
def test_alert_dispatcher_cooldown() -> None:
    from django.core.cache import cache

    cache.clear()
    mail.outbox.clear()
    send_urgent_security_alert(
        category="INCIDENT",
        title="Tamper Detected",
        details={"record": "123"},
    )
    assert len(mail.outbox) == 1

    # Immediate second identical alert must be throttled by cooldown
    send_urgent_security_alert(
        category="INCIDENT",
        title="Tamper Detected",
        details={"record": "123"},
    )
    assert len(mail.outbox) == 1


@pytest.mark.unit
def test_security_logger_writes_json(tmp_path: Path) -> None:
    log_file = tmp_path / "security.log"
    log_security_event(
        event_type="DECRYPTION_INTEGRITY_FAILED",
        severity="CRITICAL",
        details={"model": "Task", "field": "additional_notes"},
        log_path=str(log_file),
    )
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8").strip()
    data = json.loads(content)
    assert data["event_type"] == "DECRYPTION_INTEGRITY_FAILED"
    assert data["severity"] == "CRITICAL"
    assert data["details"]["model"] == "Task"
