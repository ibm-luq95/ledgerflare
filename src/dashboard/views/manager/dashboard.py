# -*- coding: utf-8 -*-#
import traceback

from django.contrib import messages
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

# from django.views.decorators.csrf import ensure_csrf_cookie
# from django.utils.decorators import method_decorator
from special_assignment.models import SpecialAssignmentProxy
from task.models import TaskProxy

logger = get_formatted_logger("bw_error_logger")


# @method_decorator(ensure_csrf_cookie, name='dispatch')
class DashboardViewBW(
    BWLoginRequiredMixin, BWManagerAccessMixin, BWSiteSettingsViewMixin, TemplateView
):
    template_name = "dashboard/manager/dashboard.html"
    http_method_names = ["get"]

    def get_context_data(self, **kwargs):
        try:
            # Call the base implementation first to get a context
            context = super().get_context_data(**kwargs)
            context.setdefault("title", _("Manager dashboard"))
            context.setdefault(
                "AUTH_TOKEN",
                (
                    self.request.session.get("auth_token")
                    if self.request.user.is_authenticated
                    else None
                ),
            )
            # DebuggingPrint.print(context)
            messages.set_level(self.request, messages.DEBUG)
            clients = ClientProxy.objects.all().order_by("-created_at")[:5]
            documents_count = Document.objects.count()
            notes_count = Note.objects.count()
            tasks_count = TaskProxy.objects.count()

            last_activities = CRUDEventProxy.objects.all().order_by("-datetime")[:4]
            special_assignments = SpecialAssignmentProxy.objects.all().order_by(
                "-created_at"
            )[:4]
            current_user = self.request.user
            manager = None
            if hasattr(current_user, "manager"):
                manager = self.request.user.manager
            elif hasattr(current_user, "bookkeeper"):
                manager = self.request.user.bookkeeper
            elif hasattr(current_user, "assistant"):
                manager = self.request.user.assistant
            queryset = manager.user.requested_assignments.filter(
                ~Q(status__in=[CON_ARCHIVED, CON_COMPLETED])
            )
            requested_special_assignments_count = queryset.count()
            context.setdefault("clients", clients)
            context.setdefault("documents_count", documents_count)
            context.setdefault("notes_count", notes_count)
            context.setdefault("tasks_count", tasks_count)
            context.setdefault(
                "requested_special_assignments_count", requested_special_assignments_count
            )
            context.setdefault("special_assignments", special_assignments)
            context.setdefault("last_activities", last_activities)

            return context
        except Exception as ex:
            DebuggingPrint.print_exception()
            raise ex
