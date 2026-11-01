"""Tests verifying that user-controlled model fields are properly HTML-escaped."""

from __future__ import annotations

import pytest
from django.core.management import call_command
from django.template import Context, Template
from django.test import RequestFactory

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from core.choices import BeachWoodUserTypeEnum


@pytest.fixture(autouse=True)
def setup_groups(db: None) -> None:
    call_command("create_groups")


@pytest.mark.django_db
class TestXssEscaping:
    """Verify that |safe filter is removed so XSS vectors are escaped by default."""

    def test_client_details_escapes_malicious_name_and_street(
        self, rf: RequestFactory
    ) -> None:
        """Malicious characters in client name and street must be entity-encoded."""
        malicious_name = '<script>alert("xss-name")</script>'
        malicious_street = "<img src=x onerror=\"alert('xss-street')\">"
        client_obj = ClientProxy.objects.create(
            name=malicious_name,
            street=malicious_street,
        )

        template_to_render = Template(
            '{% load i18n %}{% include "client/details.html" with object=client_obj %}'
        )
        request = rf.get(f"/dashboard/client/{client_obj.pk}/")
        context = Context({
            "object": client_obj,
            "client_obj": client_obj,
            "request": request,
        })
        rendered = template_to_render.render(context)

        # Raw tags must NOT exist
        assert '<script>alert("xss-name")</script>' not in rendered
        assert "<img src=x onerror=\"alert('xss-street')\">" not in rendered
        # Escaped entities must exist
        assert "&lt;script&gt;alert(&quot;xss-name&quot;)&lt;/script&gt;" in rendered

    def test_user_details_escapes_malicious_fullname(self, rf: RequestFactory) -> None:
        """Malicious characters in staff member fullname must be entity-encoded."""
        user = BWUser.objects.create_user(
            email="victim_staff@example.com",
            password="ValidPassword123!",
            first_name="<b>XSS</b>",
            last_name="Staff",
            user_type=BeachWoodUserTypeEnum.BOOKKEEPER,
        )

        template_to_render = Template(
            '{% load i18n %}{% include "beach_wood_user/details.html" with object=user %}'
        )
        request = rf.get(f"/dashboard/staff/{user.pk}/")
        context = Context({"object": user, "user": user, "request": request})
        rendered = template_to_render.render(context)

        assert "<b>XSS</b>" not in rendered
        assert "&lt;b&gt;XSS&lt;/b&gt;" in rendered
