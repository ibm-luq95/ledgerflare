from __future__ import annotations

from typing import Any

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import ListView

from core.cache import BWSiteSettingsViewMixin
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.constants.users import CON_ASSISTANT, CON_BOOKKEEPER, CON_CFO, CON_MANAGER
from core.utils.html_sanitizer import sanitize_html
from core.views.mixins import BWBaseListViewMixin, BWLoginRequiredMixin
from discussion.models import DiscussionProxy
from job.models import JobProxy
from special_assignment.models import SpecialAssignmentProxy


def _check_target_access(user: Any, target_obj: Any) -> bool:
    """Verify if user has permission to post discussions on target object."""
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.user_type in (CON_MANAGER, CON_ASSISTANT):
        return True

    if user.user_type == CON_BOOKKEEPER and hasattr(user, "bookkeeper"):
        bk = user.bookkeeper
        if (
            hasattr(target_obj, "bookkeepers")
            and target_obj.bookkeepers.filter(pk=bk.pk).exists()
        ):
            return True
        if (
            hasattr(target_obj, "client")
            and target_obj.client
            and hasattr(target_obj.client, "bookkeepers")
            and target_obj.client.bookkeepers.filter(pk=bk.pk).exists()
        ):
            return True
        if hasattr(target_obj, "bookkeeper") and target_obj.bookkeeper == bk:
            return True
        if hasattr(target_obj, "assigned_to") and target_obj.assigned_to == user:
            return True
        return False

    if user.user_type == CON_CFO and hasattr(user, "cfo"):
        cfo = user.cfo
        if hasattr(target_obj, "cfos") and target_obj.cfos.filter(pk=cfo.pk).exists():
            return True
        if (
            hasattr(target_obj, "client")
            and target_obj.client
            and hasattr(target_obj.client, "cfos")
            and target_obj.client.cfos.filter(pk=cfo.pk).exists()
        ):
            return True
        return False

    return False


class DiscussionCreateHtmxView(BWLoginRequiredMixin, View):
    """Secure HTMX endpoint for posting discussions to jobs and special assignments."""

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        user = request.user
        raw_body = request.POST.get("body", "").strip()
        attachment = request.FILES.get("attachment")
        special_assignment_id = request.POST.get("special_assignment", "").strip()
        job_id = request.POST.get("job", "").strip()

        if not raw_body and not attachment:
            return HttpResponseBadRequest(_("Message body or attachment is required."))

        if attachment:
            from core.constants.file_types_validation import IMAGES_AND_DOCS_FT
            from core.utils import FileValidator
            from django.core.exceptions import ValidationError

            validator = FileValidator(
                max_size=1024 * 1024 * 100, content_types=IMAGES_AND_DOCS_FT
            )
            try:
                validator(attachment)
            except ValidationError as ve:
                return HttpResponseBadRequest(str(ve))

        clean_body = sanitize_html(raw_body)
        target_special_assignment = None
        target_job = None

        if special_assignment_id:
            target_special_assignment = get_object_or_404(
                SpecialAssignmentProxy, pk=special_assignment_id
            )
            if not _check_target_access(user, target_special_assignment):
                raise PermissionDenied(
                    _("You do not have access to this special assignment.")
                )

        elif job_id:
            target_job = get_object_or_404(JobProxy, pk=job_id)
            if not _check_target_access(user, target_job):
                raise PermissionDenied(_("You do not have access to this job."))

        else:
            return HttpResponseBadRequest(
                _("Target special assignment or job must be specified.")
            )

        # Initialize and save discussion with system-locked sender
        discussion = DiscussionProxy(
            body=clean_body,
            sender=user,
            special_assignment=target_special_assignment,
            job=target_job,
            attachment=attachment if attachment else None,
        )

        # Automatically associate staff role reference
        match user.user_type:
            case "manager" if hasattr(user, "manager"):
                discussion.manager = user.manager.get_proxy_model()
            case "bookkeeper" if hasattr(user, "bookkeeper"):
                discussion.bookkeeper = user.bookkeeper.get_proxy_model()
            case "assistant" if hasattr(user, "assistant"):
                discussion.assistant = user.assistant.get_proxy_model()

        discussion.save()

        return render(
            request,
            "bw_ui_components/discussion/single_message.html",
            {"discussion": discussion, "request": request},
        )


class DiscussionListView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    ListView,
):
    permission_required = "discussion.can_view_list"
    template_name = "core/crudl/list.html"
    model = DiscussionProxy
    paginate_by = LIST_VIEW_PAGINATE_BY
    list_type = "list"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["title"] = _("Discussions")
        context.setdefault("list_type", self.list_type)
        context.setdefault("page_header", _("discussions".title()))
        context.setdefault("component_path", "bw_components/discussion/table_list.html")
        context.setdefault(
            "subtitle",
            _(
                "Collaborative discussion threads, client consultations, and team communication."
            ),
        )
        context.setdefault("actions_base_url", "dashboard:discussion")
        context.setdefault("filter_cancel_url", "dashboard:discussion:list")
        context.setdefault("table_header_title", _("C"))
        context.setdefault(
            "table_header_subtitle",
            _("Active consultation threads, case discussions, and team messages."),
        )
        context.setdefault("is_show_create_btn", False)
        context.setdefault("pagination_list_url_name", "dashboard:discussion:list")
        context.setdefault("is_filters_enabled", False)
        context.setdefault("is_actions_menu_enabled", False)
        context.setdefault("is_header_enabled", True)
        context.setdefault("is_footer_enabled", True)
        context.setdefault("actions_items", "details,update,delete")
        context.setdefault("base_url_name", "dashboard:discussion")
        context.setdefault("empty_label", _("discussions"))
        context.setdefault("extra_context", {})
        context.setdefault("show_info_icon", True)
        context.setdefault(
            "info_details",
            {
                "tooltip_txt": BW_INFO_MODAL_CSS_CLASSES.get("discussion", {}).get(
                    "tooltip_txt"
                ),
                "modal_css_id": BW_INFO_MODAL_CSS_CLASSES.get("discussion", {}).get(
                    "cssID"
                ),
            },
        )
        context.setdefault("filter_form_id", "discussionFilterForm")
        return context
