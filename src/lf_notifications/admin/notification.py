# -*- coding: utf-8 -*-#
from __future__ import annotations

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.admin import BWBaseAdminModelMixin
from lf_notifications.models import NotificationProxy

from django.urls import reverse
from django.utils.html import format_html

@admin.register(NotificationProxy)
class NotificationAdmin(BWBaseAdminModelMixin):
    list_display = [
        "actor",
        "verb",
        "message_template",
        "content_type",
        "object_admin_link",
        "created_at",
    ]
    list_filter = ["verb", "content_type"] + BWBaseAdminModelMixin.list_filter
    search_fields = ["message_template", "actor__email", "actor__first_name", "actor__last_name"]
    readonly_fields = ["object_admin_link"]

    @admin.display(description=_("Linked Object"))
    def object_admin_link(self, obj: NotificationProxy) -> str:
        if obj.content_type and obj.object_id:
            try:
                # Try to get the actual object to display its __str__
                target_obj = obj.content_object
                display_text = str(target_obj) if target_obj else f"{obj.content_type.model}: {obj.object_id}"
                
                model_name = obj.content_type.model.lower().replace(" ", "")
                app_label = obj.content_type.app_label
                try:
                    url = reverse(f"admin:{app_label}_{model_name}_change", args=[obj.object_id])
                except Exception:
                    url = reverse(f"admin:{app_label}_{model_name}proxy_change", args=[obj.object_id])
                
                return format_html(
                    '{} <a href="{}" class="related-lookup" title="View details" style="display:inline-block; vertical-align:middle; margin-left:5px;">'
                    '<img src="/static/admin/img/icon-viewlink.svg" alt="View" style="width:16px; height:16px;">'
                    '</a>',
                    display_text,
                    url,
                )
            except Exception:
                return f"{obj.content_type.model}: {obj.object_id}"
        return _("No object linked")
