from __future__ import annotations

import pytest
from django.contrib.auth.models import Permission
from django.core.files.base import ContentFile
from django.test import Client
from django.urls import reverse
from model_bakery import baker

from beach_wood_user.models import BWUser
from document.models import Document


@pytest.fixture
def manager_user_with_perms(db: None) -> BWUser:
    user = baker.make(BWUser, is_staff=True, is_superuser=False, user_type="")
    can_view = Permission.objects.filter(
        codename="can_view_list", content_type__app_label="document"
    ).first()
    assert can_view is not None
    user.user_permissions.add(can_view)
    return user


@pytest.mark.django_db
def test_document_list_renders_view_action_button(
    client: Client, manager_user_with_perms: BWUser
) -> None:
    doc = Document.objects.create(
        title="Tax Return 2025",
        document_file=ContentFile(b"%PDF-1.4 sample", name="tax.pdf"),
    )

    client.force_login(manager_user_with_perms)
    url = reverse("dashboard:document:list")
    response = client.get(url)

    assert response.status_code == 200
    expected_view_url = reverse("dashboard:document:view", kwargs={"pk": doc.pk})
    content = response.content.decode("utf-8")

    assert expected_view_url in content
    assert 'target="_blank"' in content
    assert 'rel="noopener noreferrer"' in content
