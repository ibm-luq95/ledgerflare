"""Tests for secure HTML formatting in templatetags and admin helpers."""

from __future__ import annotations

import pytest
from django.contrib.contenttypes.models import ContentType
from django.template import Context

from bw_ui_components.templatetags.elements.js_modal import bw_js_modal
from client.models import ClientProxy
from lf_notifications.admin.notification import NotificationAdmin
from lf_notifications.models import Notification


@pytest.mark.django_db
class TestSecureHtmlFormatting:
    """Verify that format_html is used to escape injected strings in markup."""

    def test_bw_js_modal_escapes_extra_hidden_inputs(self) -> None:
        """Malicious values in extra_hidden_inputs must be HTML-escaped."""
        context = Context({})
        malicious_val = "123' onclick='alert(1)' data-foo='"
        raw_inputs = str({"client_id": malicious_val})

        result = bw_js_modal(context, extra_hidden_inputs=raw_inputs)
        markup_list = result["extra_hidden_inputs_markup_list"]
        assert len(markup_list) == 1
        rendered_input = str(markup_list[0])

        # Malicious attribute injection must be entity-encoded
        assert "onclick='alert(1)'" not in rendered_input
        assert (
            "&#x27;" in rendered_input
            or "&quot;" in rendered_input
            or "&#39;" in rendered_input
        )

    def test_notification_admin_escapes_target_object_repr(self) -> None:
        """NotificationAdmin.get_target_object must escape dangerous object __str__ representations."""
        malicious_client = ClientProxy.objects.create(
            name="<script>alert('admin-xss')</script>"
        )
        ct = ContentType.objects.get_for_model(ClientProxy)
        notification = Notification.objects.create(
            content_type=ct,
            object_id=malicious_client.pk,
            verb="created",
            message_template="Alert message",
        )

        admin_instance = NotificationAdmin(Notification, None)
        output = admin_instance.object_admin_link(notification)

        # Raw script tags must NOT be present
        assert "<script>alert('admin-xss')</script>" not in output
        assert (
            "&lt;script&gt;alert(&#x27;admin-xss&#x27;)&lt;/script&gt;" in output
            or "&lt;script&gt;" in output
        )
