"""Structured security event logger outputting Wazuh-compatible JSON."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from django.conf import settings
from django.http import HttpRequest


def get_client_ip(request: HttpRequest) -> str:
    """Extract true client IP taking X-Forwarded-For into account."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "127.0.0.1")


def log_security_event(
    event_type: str,
    severity: str,
    details: dict[str, Any],
    request: HttpRequest | None = None,
    log_path: str | None = None,
) -> None:
    """Write structured JSON security log entry to disk with stderr fallback."""
    if log_path is None:
        base_dir = getattr(settings, "BASE_DIR", None)
        if base_dir:
            parent_dir = base_dir.parent if hasattr(base_dir, "parent") else base_dir
            target_dir = Path(str(parent_dir)) / "logs"
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / "security.log"
        else:
            target_path = Path("logs/security.log")
    else:
        target_path = Path(log_path)

    user_id = None
    username = None
    ip_address = "127.0.0.1"
    method = None
    path = None
    status_code = None

    if request is not None:
        ip_address = get_client_ip(request)
        method = request.method
        path = request.path
        if hasattr(request, "user") and request.user.is_authenticated:
            user_id = str(getattr(request.user, "pk", ""))
            user = request.user
            username = getattr(user, "email", None) or getattr(user, "username", None)
        status_code = getattr(request, "_security_status_code", None)

    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "severity": severity,
        "user_id": user_id,
        "username": username,
        "ip_address": ip_address,
        "method": method,
        "path": path,
        "status_code": status_code,
        "details": details,
    }

    line = json.dumps(record, default=str) + "\n"
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with target_path.open("a", encoding="utf-8") as f:
            f.write(line)
    except OSError as err:
        sys.stderr.write(f"SECURITY_LOG_FAILURE: {err} | {line}")
