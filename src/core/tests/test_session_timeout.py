from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

from core.middleware.session_timeout import SessionInactivityTimeoutMiddleware


@pytest.mark.django_db
def test_active_session_updates_timestamp() -> None:
    from core.middleware.session_timeout import SessionInactivityTimeoutMiddleware

    rf = RequestFactory()
    request = rf.get("/dashboard/")
    user = get_user_model().objects.create_user(
        email="staff1@example.com", password="password"
    )
    request.user = user

    SessionMiddleware(lambda r: None).process_request(request)
    now = datetime.now(UTC)
    request.session["last_activity"] = (now - timedelta(minutes=10)).isoformat()

    middleware = SessionInactivityTimeoutMiddleware(lambda r: None)
    middleware(request)

    assert datetime.fromisoformat(request.session["last_activity"]) >= now


@pytest.mark.django_db
def test_inactive_session_expires_and_redirects() -> None:
    from core.middleware.session_timeout import SessionInactivityTimeoutMiddleware

    rf = RequestFactory()
    request = rf.get("/dashboard/")
    user = get_user_model().objects.create_user(
        email="staff2@example.com", password="password"
    )
    request.user = user

    SessionMiddleware(lambda r: None).process_request(request)
    now = datetime.now(UTC)
    request.session["last_activity"] = (now - timedelta(minutes=31)).isoformat()

    middleware = SessionInactivityTimeoutMiddleware(lambda r: None)
    response = middleware(request)

    assert response is not None
    assert response.status_code == 302
    assert "reason=timeout" in response.url


@pytest.mark.django_db
def test_exempt_path_does_not_update_timestamp() -> None:
    from core.middleware.session_timeout import SessionInactivityTimeoutMiddleware

    rf = RequestFactory()
    request = rf.get("/api/notifications/unread-count/")
    user = get_user_model().objects.create_user(
        email="staff3@example.com", password="password"
    )
    request.user = user

    SessionMiddleware(lambda r: None).process_request(request)
    ten_mins_ago = (datetime.now(UTC) - timedelta(minutes=10)).isoformat()
    request.session["last_activity"] = ten_mins_ago

    middleware = SessionInactivityTimeoutMiddleware(lambda r: None)
    middleware(request)

    assert request.session["last_activity"] == ten_mins_ago


@pytest.mark.django_db
def test_anonymous_user_ignored() -> None:
    rf = RequestFactory()
    request = rf.get("/dashboard/")
    request.user = AnonymousUser()

    SessionMiddleware(lambda r: None).process_request(request)
    middleware = SessionInactivityTimeoutMiddleware(lambda r: "ok")
    resp = middleware(request)
    assert resp == "ok"
    assert "last_activity" not in request.session


@pytest.mark.django_db
def test_ajax_json_session_expired_returns_401() -> None:
    rf = RequestFactory()
    request = rf.get(
        "/api/tasks/",
        HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        HTTP_ACCEPT="application/json",
    )
    user = get_user_model().objects.create_user(
        email="ajax_staff@example.com", password="password"
    )
    request.user = user

    SessionMiddleware(lambda r: None).process_request(request)
    now = datetime.now(UTC)
    request.session["last_activity"] = (now - timedelta(minutes=45)).isoformat()

    middleware = SessionInactivityTimeoutMiddleware(lambda r: None)
    response = middleware(request)

    assert response is not None
    assert response.status_code == 401
    data = json.loads(response.content)
    assert data["error"] == "session_expired"
    assert "reason=timeout" in data["redirect"]


@pytest.mark.django_db
def test_malformed_timestamp_does_not_crash() -> None:
    rf = RequestFactory()
    request = rf.get("/dashboard/")
    user = get_user_model().objects.create_user(
        email="staff_malformed@example.com", password="password"
    )
    request.user = user

    SessionMiddleware(lambda r: None).process_request(request)
    request.session["last_activity"] = "INVALID_TIMESTAMP_STRING"

    middleware = SessionInactivityTimeoutMiddleware(lambda r: None)
    middleware(request)

    # Malformed timestamp is handled safely without error, resetting to fresh timestamp
    assert datetime.fromisoformat(request.session["last_activity"]) is not None


@pytest.mark.django_db
def test_background_header_does_not_update_timestamp() -> None:
    from core.middleware.session_timeout import SessionInactivityTimeoutMiddleware

    rf = RequestFactory()
    request = rf.get("/some/other/path/", HTTP_X_BACKGROUND_REQUEST="true")
    user = get_user_model().objects.create_user(
        email="staff4@example.com", password="password"
    )
    request.user = user

    SessionMiddleware(lambda r: None).process_request(request)
    ten_mins_ago = (datetime.now(UTC) - timedelta(minutes=10)).isoformat()
    request.session["last_activity"] = ten_mins_ago

    middleware = SessionInactivityTimeoutMiddleware(lambda r: None)
    middleware(request)

    assert request.session["last_activity"] == ten_mins_ago
