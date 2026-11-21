import pytest
from django.test import Client
from django.urls import reverse

@pytest.mark.django_db
def test_full_security_hardening_suite(client: Client):
    # 1. Base response checks for security headers
    res = client.get("/")
    assert res.status_code in (200, 302)
    assert "Content-Security-Policy" in res.headers
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    
    # 2. Axes lockout test check
    login_url = reverse("auth:login")
    for _ in range(5):
        client.post(login_url, {"email": "baduser@example.com", "password": "wrongpassword", "user_type": "manager"})
    locked_res = client.post(login_url, {"email": "baduser@example.com", "password": "wrongpassword", "user_type": "manager"})
    assert locked_res.status_code in (403, 429)
