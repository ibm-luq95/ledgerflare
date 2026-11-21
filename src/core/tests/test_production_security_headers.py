import pytest
from django.test import override_settings, Client

@pytest.mark.django_db
@override_settings(
    SECURE_HSTS_SECONDS=31536000,
    X_FRAME_OPTIONS="DENY",
    SECURE_CONTENT_TYPE_NOSNIFF=True,
    SECURE_REFERRER_POLICY="strict-origin-when-cross-origin",
    SESSION_COOKIE_SAMESITE="Lax",
    CSRF_COOKIE_SAMESITE="Lax"
)
def test_production_security_headers(client: Client):
    response = client.get("/")
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
