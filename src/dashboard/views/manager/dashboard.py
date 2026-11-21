# -*- coding: utf-8 -*-#
from __future__ import annotations

from typing import Any
from django.db.models import Q
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from client.models import ClientProxy
from core.cache import BWSiteSettingsViewMixin
from core.constants.status_labels import CON_ARCHIVED, CON_COMPLETED
from core.models import CRUDEventProxy
from core.utils import get_formatted_logger
from core.utils.developments.debugging_print_object import DebuggingPrint
from core.views.mixins import BWLoginRequiredMixin, BWManagerAccessMixin
from document.models import Document
from note.models import Note
from special_assignment.models import SpecialAssignmentProxy
from task.models import TaskProxy

logger = get_formatted_logger("bw_error_logger")


class DashboardViewBW(
    BWLoginRequiredMixin, BWManagerAccessMixin, BWSiteSettingsViewMixin, TemplateView
):
    template_name = "dashboard/manager/dashboard.html"
    http_method_names = ["get"]

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        try:
            context = super().get_context_data(**kwargs)
            context.setdefault("title", _("Manager dashboard"))

            user = self.request.user
            context.setdefault(
                "AUTH_TOKEN",
                (
                    self.request.session.get("auth_token")
                    if user.is_authenticated
                    else None
                ),
            )

            # 1. Compact client projection for the sidebar feed
            clients = ClientProxy.objects.only(
                "id",
                "name",
                "is_active",
                "email",
                "phone_number",
                "company_logo",
                "created_at",
            ).order_by("-created_at")[:6]

            # 2. Model counts
            documents_count = Document.objects.count()
            notes_count = Note.objects.count()
            tasks_count = TaskProxy.objects.count()

            # 3. Eager-load actor and content_type to eliminate activity timeline N+1 queries
            last_activities = CRUDEventProxy.objects.select_related(
                "actor", "content_type"
            ).order_by("-timestamp")[:7]

            # 4. Eager-load assigned_by and client to eliminate assignment feed N+1 queries
            special_assignments = SpecialAssignmentProxy.objects.select_related(
                "assigned_by", "client"
            ).order_by("-created_at")[:5]

            # 5. Direct count query for user's requested assignments without relation traversal
            requested_special_assignments_count = (
                user.requested_assignments.filter(
                    ~Q(status__in=[CON_ARCHIVED, CON_COMPLETED])
                ).count()
                if user.is_authenticated
                else 0
            )

            context.setdefault("clients", clients)
            context.setdefault("documents_count", documents_count)
            context.setdefault("notes_count", notes_count)
            context.setdefault("tasks_count", tasks_count)
            context.setdefault(
                "requested_special_assignments_count",
                requested_special_assignments_count,
            )
            context.setdefault("special_assignments", special_assignments)
            context.setdefault("last_activities", last_activities)

            return context
        except Exception as ex:
            DebuggingPrint.print_exception()
            raise ex
