from __future__ import annotations

from pathlib import Path

import pytest
from django.contrib.auth.models import Permission
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from model_bakery import baker

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from core.constants.site_settings import SITE_SETTINGS_DB_SLUG
from core.constants.users import CON_BOOKKEEPER, CON_MANAGER
from document.models import Document
from site_settings.models import SiteSettings


@pytest.fixture(autouse=True)
def setup_environment(db: None) -> None:
    call_command("create_groups")
    SiteSettings.objects.get_or_create(
        slug=SITE_SETTINGS_DB_SLUG,
        defaults={"can_bookkeepers_login": True, "name": "Beach Wood"},
    )


@pytest.fixture
def test_user(db: None) -> BWUser:
    user = baker.make(
        BWUser, is_staff=True, is_superuser=False, user_type=CON_MANAGER
    )
    user.user_permissions.clear()
    can_view = Permission.objects.filter(
        codename="can_view_list", content_type__app_label="document"
    ).first()
    assert can_view is not None
    user.user_permissions.add(can_view)
    return user


@pytest.fixture
def unprivileged_user(db: None) -> BWUser:
    user = baker.make(BWUser, is_staff=False, is_superuser=False, user_type="")
    user.user_permissions.clear()
    return user


@pytest.fixture
def pdf_document(db: None) -> Document:
    content = b"%PDF-1.5 Sample PDF file content for viewer tests." + (b"A" * 2000)
    return Document.objects.create(
        title="Quarterly Report",
        document_file=ContentFile(content, name="report.pdf"),
    )


@pytest.fixture
def svg_document(db: None) -> Document:
    content = b"<svg><script>alert(1)</script></svg>"
    return Document.objects.create(
        title="Logo SVG",
        document_file=ContentFile(content, name="logo.svg"),
    )


@pytest.mark.django_db
def test_anonymous_redirected_to_login(client: Client, pdf_document: Document) -> None:
    url = reverse("dashboard:document:view", kwargs={"pk": pdf_document.pk})
    response = client.get(url)
    assert response.status_code == 302
    assert "/auth/login" in response.url


@pytest.mark.django_db
def test_unauthorized_user_forbidden(
    client: Client, unprivileged_user: BWUser, pdf_document: Document
) -> None:
    client.force_login(unprivileged_user)
    url = reverse("dashboard:document:view", kwargs={"pk": pdf_document.pk})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_authorized_user_inline_view_200(
    client: Client, test_user: BWUser, pdf_document: Document
) -> None:
    client.force_login(test_user)
    url = reverse("dashboard:document:view", kwargs={"pk": pdf_document.pk})
    response = client.get(url)

    assert response.status_code == 200
    assert response["Accept-Ranges"] == "bytes"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert "sandbox allow-same-origin;" in response["Content-Security-Policy"]
    assert "allow-scripts" not in response["Content-Security-Policy"]
    assert response.headers["Content-Disposition"].startswith("inline")
    assert response.headers["Content-Type"] == "application/pdf"

    content = b"".join(response.streaming_content)
    assert content.startswith(b"%PDF-1.5")


@pytest.mark.django_db
def test_range_request_partial_content_206(
    client: Client, test_user: BWUser, pdf_document: Document
) -> None:
    client.force_login(test_user)
    url = reverse("dashboard:document:view", kwargs={"pk": pdf_document.pk})

    # Request bytes 0 to 99 (100 bytes)
    response = client.get(url, HTTP_RANGE="bytes=0-99")

    assert response.status_code == 206
    assert response["Accept-Ranges"] == "bytes"
    total_len = pdf_document.document_file.size
    assert response["Content-Range"] == f"bytes 0-99/{total_len}"
    assert response["Content-Length"] == "100"

    content = b"".join(response.streaming_content)
    assert len(content) == 100
    assert content == b"%PDF-1.5 Sample PDF file content for viewer tests." + (
        b"A" * 50
    )


@pytest.mark.django_db
def test_range_suffix_request_206(
    client: Client, test_user: BWUser, pdf_document: Document
) -> None:
    client.force_login(test_user)
    url = reverse("dashboard:document:view", kwargs={"pk": pdf_document.pk})

    # Request final 50 bytes
    response = client.get(url, HTTP_RANGE="bytes=-50")

    assert response.status_code == 206
    total_len = pdf_document.document_file.size
    start = total_len - 50
    end = total_len - 1
    assert response["Content-Range"] == f"bytes {start}-{end}/{total_len}"
    assert response["Content-Length"] == "50"

    content = b"".join(response.streaming_content)
    assert len(content) == 50
    assert content == b"A" * 50


@pytest.mark.django_db
def test_range_out_of_bounds_416(
    client: Client,
    test_user: BWUser,
    pdf_document: Document,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from core.crypto.stream import EncryptedStreamReader

    client.force_login(test_user)
    url = reverse("dashboard:document:view", kwargs={"pk": pdf_document.pk})

    closed = False
    orig_close = EncryptedStreamReader.close

    def tracked_close(self: EncryptedStreamReader) -> None:
        nonlocal closed
        closed = True
        orig_close(self)

    monkeypatch.setattr(EncryptedStreamReader, "close", tracked_close)

    response = client.get(url, HTTP_RANGE="bytes=999999999-")
    assert response.status_code == 416
    total_len = pdf_document.document_file.size
    assert response["Content-Range"] == f"bytes */{total_len}"
    assert closed is True


@pytest.mark.django_db
def test_svg_file_forced_to_download_attachment(
    client: Client, test_user: BWUser, svg_document: Document
) -> None:
    client.force_login(test_user)
    url = reverse("dashboard:document:view", kwargs={"pk": svg_document.pk})
    response = client.get(url)

    assert response.status_code == 200
    # Must be forced to download as attachment to prevent Stored XSS
    assert response.headers["Content-Disposition"].startswith("attachment")
    assert "Content-Security-Policy" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"


@pytest.mark.django_db
def test_unassigned_bookkeeper_denied_access_403(
    client: Client, pdf_document: Document
) -> None:
    assigned_client = ClientProxy.objects.create(name="Assigned Corp")
    pdf_document.client = assigned_client
    pdf_document.save()

    bk_user_unassigned = BWUser.objects.create_user(
        email="bk_unassigned@example.com",
        password="ValidPassword123!",
        user_type=CON_BOOKKEEPER,
    )
    can_view = Permission.objects.filter(
        codename="can_view_list", content_type__app_label="document"
    ).first()
    assert can_view is not None
    bk_user_unassigned.user_permissions.add(can_view)

    client.force_login(bk_user_unassigned)
    url = reverse("dashboard:document:view", kwargs={"pk": pdf_document.pk})
    response = client.get(url)
    assert response.status_code == 403

    bk_user_assigned = BWUser.objects.create_user(
        email="bk_assigned@example.com",
        password="ValidPassword123!",
        user_type=CON_BOOKKEEPER,
    )
    bk_user_assigned.user_permissions.add(can_view)
    assigned_client.bookkeepers.add(
        bk_user_assigned.bookkeeper.get_proxy_model()
    )

    client.force_login(bk_user_assigned)
    response_assigned = client.get(url)
    assert response_assigned.status_code == 200
