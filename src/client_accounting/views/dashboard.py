from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView

from client.forms import AssignBookkeeperForm
from client.forms import ClientForm
from client.forms import ClientMiniForm
from client.forms.assign_cfo import AssignCFOForm
from client.models import ClientProxy
from client_account.forms import ClientAccountForm
from core.cache import BWSiteSettingsViewMixin
from core.config.forms import BWFormRenderer
from core.constants.status_labels import CON_ENABLED
from core.constants.users import CON_ASSISTANT
from core.constants.users import CON_MANAGER
from core.views.mixins import BWLoginRequiredMixin
from core.views.mixins.base_list_view import BWSectionDescriptionHelperMixin
from document.forms import DocumentForm
from important_contact.forms import ImportantContactForm
from job.forms import JobMiniForm
from note.forms import NoteForm
from special_assignment.forms import MiniSpecialAssignmentForm
from task.forms import TaskForm


class ClientDashboardView(
    PermissionRequiredMixin,
    UserPassesTestMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWSectionDescriptionHelperMixin,
    DetailView,
):
    template_name = "client_accounting/dashboard.html"

    model = ClientProxy
    permission_required = "client.view_client"
    permission_denied_message = _("You do not have permission to access this page.")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _(f"Client - {self.get_object().name}"))
        job_form = JobMiniForm(
            initial={"client": self.get_object().pk},
            client=self.get_object(),
        )
        important_contact_form = ImportantContactForm(
            initial={"client": self.get_object()},
            renderer=BWFormRenderer(),
        )
        client_form = ClientForm(
            instance=self.get_object(),
            renderer=BWFormRenderer(),
            removed_fields=[
                "categories",
                "bookkeepers",
                "important_contacts",
                "status",
            ],
        )
        client_mini_form = ClientMiniForm()
        task_form = TaskForm(
            initial={"client": self.get_object()},
            # removed_fields=["job"],
            hidden_fields=["job"],
            renderer=BWFormRenderer(),
        )
        document_form = DocumentForm(
            initial={"client": self.get_object(), "document_section": "client"},
            renderer=BWFormRenderer(),
            removed_fields=["task", "status", "job"],
            hidden_inputs={"field_names": ["client"]},
        )
        note_form = NoteForm(
            renderer=BWFormRenderer(),
            initial={"client": self.get_object()},
            removed_fields=["task", "job"],
            hidden_inputs={"field_names": ["client"]},
        )
        special_assignment_form = MiniSpecialAssignmentForm(
            renderer=BWFormRenderer(),
            initial={
                "assigned_by": self.request.user.pk,
                "client": self.get_object().pk,
            },
        )
        client_account_form = ClientAccountForm(
            initial={"client": self.get_object(), "status": CON_ENABLED},
            renderer=BWFormRenderer(),
            hidden_inputs={"field_names": ["client", "status"]},
        )
        client_assign_bookkeeper_form = AssignBookkeeperForm(
            renderer=BWFormRenderer(), client=self.get_object()
        )
        client_assign_cfo_form = AssignCFOForm(
            renderer=BWFormRenderer(), client=self.get_object()
        )
        context.setdefault("job_form", job_form)
        # context.setdefault("job_status_choices", JobStatusEnum.choices)
        context.setdefault("task_form", task_form)
        context.setdefault("document_form", document_form)
        context.setdefault("client_form", client_form)
        context.setdefault("important_contact_form", important_contact_form)
        context.setdefault("note_form", note_form)
        context.setdefault("client_mini_form", client_mini_form)
        context.setdefault("special_assignment_form", special_assignment_form)
        context.setdefault("client_account_form", client_account_form)
        context.setdefault(
            "client_assign_bookkeeper_form", client_assign_bookkeeper_form
        )
        context.setdefault("client_assign_cfo_form", client_assign_cfo_form)
        return context

    def test_func(self) -> bool:
        user_type = self.request.user.user_type
        if user_type in {CON_MANAGER, CON_ASSISTANT}:
            return True
        else:
            bookkeeper = self.request.user.bookkeeper
            check = self.get_object().bookkeepers.filter(pk=bookkeeper.pk).exists()
            return check
