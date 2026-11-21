"""Urgent incident alerting pipeline with deduplication cooldown."""

from __future__ import annotations

import contextlib
import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail


def send_urgent_security_alert(
    category: str, title: str, details: dict[str, Any]
) -> None:
    """Send alert email to administrator with a 15-minute cooldown."""
    signature_data = f"{category}:{title}:{json.dumps(details, sort_keys=True)}"
    digest = hashlib.sha256(signature_data.encode()).hexdigest()
    cache_key = f"alert_cooldown:{category}:{digest}"

    if cache.get(cache_key):
        return

    cache.set(cache_key, True, timeout=900)

    recipient = getattr(
        settings, "MANAGER_MAIN_EMAIL", "manager@beachwoodfinancial.com"
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@ledgerflare.com")
    subject = f"[URGENT SECURITY ALERT - {category}] {title}"
    body = (
        "URGENT SECURITY ALERT\n"
        "=====================\n"
        f"Category: {category}\n"
        f"Title: {title}\n"
        f"Timestamp: {datetime.now(UTC).isoformat()}\n\n"
        "Details:\n"
        f"{json.dumps(details, indent=2, default=str)}\n"
    )

    with contextlib.suppress(Exception):
        send_mail(
            subject=subject,
            message=body,
            from_email=from_email,
            recipient_list=[recipient],
            fail_silently=True,
        )
