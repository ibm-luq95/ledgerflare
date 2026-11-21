"""Tests for DOM password masking and update form behavior."""

from __future__ import annotations

import pytest
from django.template import Context, Template
from django.test import RequestFactory
from django.urls import reverse

from client.models import ClientProxy
from client_account.forms import ClientAccountForm
from client_account.models import ClientAccountProxy


@pytest.mark.django_db
class TestDomPasswordMasking:
    """Verify that plaintext passwords are never rendered into HTML DOM."""

    def test_client_account_table_masks_password(self, rf: RequestFactory) -> None:
        """Table list row must not output cleartext password in value attribute."""
        client_obj = ClientProxy.objects.create(name="Secure Client")
        account = ClientAccountProxy.objects.create(
            client=client_obj,
            account_name="Sensitive Bank",
            account_password="SuperSecretPasswordXYZ999!",
        )

        template_to_render = Template(
            '{% load i18n %}{% include "bw_components/client_account/table_list.html" with object_list=accounts %}'
        )
        request = rf.get("/dashboard/client-account/")
        context = Context({
            "object_list": [account],
            "accounts": [account],
            "request": request,
            "base_url_name": "dashboard:client_account",
        })
        rendered = template_to_render.render(context)

        # Plaintext password must NOT appear anywhere in the rendered HTML
        assert "SuperSecretPasswordXYZ999!" not in rendered
        # Must contain placeholder masking
        assert "••••••••" in rendered
        # Must contain reveal endpoint attribute
        reveal_url = reverse(
            "dashboard:client_account:api:reveal-password", kwargs={"pk": account.pk}
        )
        assert reveal_url in rendered

    def test_client_account_update_form_preserves_password_when_blank(self) -> None:
        """Submitting empty password on update keeps existing encrypted password intact."""
        client_obj = ClientProxy.objects.create(name="Preserve Client")
        account = ClientAccountProxy.objects.create(
            client=client_obj,
            account_name="Existing Portal",
            account_password="OriginalSecurePassword!",
        )

        form_data = {
            "client": str(client_obj.pk),
            "account_name": "Updated Portal Name",
            "account_url": "https://bank.example.com",
            "account_username": "portal_admin",
            "status": "enabled",
            "account_password": "",  # left blank
        }
        form = ClientAccountForm(
            data=form_data,
            instance=account,
            is_update=True,
            updated_object=account,
        )
        assert form.is_valid(), form.errors
        saved_account = form.save()
        assert saved_account.decrypted_account_password == "OriginalSecurePassword!"
