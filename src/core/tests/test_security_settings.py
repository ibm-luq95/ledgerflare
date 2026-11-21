from __future__ import annotations

import pytest
from django.conf import settings


@pytest.mark.unit
def test_security_settings_loaded() -> None:
    assert hasattr(settings, "CONTENT_ENCRYPTION_KEY")
    assert hasattr(settings, "MALWARE_SCANNER_ENABLED")
    assert hasattr(settings, "CLAMAV_SOCKET_PATH")
    assert settings.CLAMAV_SOCKET_PATH == "/var/run/clamav/clamd.ctl"
    assert settings.SESSION_INACTIVITY_TIMEOUT_SECONDS == 1800
    assert isinstance(settings.SESSION_INACTIVITY_EXEMPT_PATHS, list)
    assert hasattr(settings, "SENDGRID_API_KEY")
