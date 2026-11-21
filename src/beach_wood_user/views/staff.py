"""Staff views module for profile, details, and password administration."""
from __future__ import annotations

from typing import Any, ClassVar

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.forms import BaseForm
from django.http import HttpRequest, HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import DetailView, FormView
from django.views.generic.detail import SingleObjectMixin

from assistant.forms import AssistantForm
from beach_wood_user.forms import (
    BWPermissionsForm,
    ForceChangePasswordForm,
    ProfileForm,
)
from beach_wood_user.models import BWUser
from bookkeeper.forms import BookkeeperForm
from client.models import ClientProxy
from core.api.throttling import AuthEndpointRateThrottle
from core.config.forms import BWFormRenderer
from core.constants.users import (
    ASSISTANT_FULL_MANAGER_PERMISSION_WITH_MODEL_NAME,
    CON_ASSISTANT,
    CON_BOOKKEEPER,
    CON_MANAGER,
)
from core.views.mixins import BWLoginRequiredMixin, ThrottledViewMixin
from manager.forms import ManagerForm
from special_assignment.forms import MiniSpecialAssignmentForm
from staff_briefcase.forms import (
    BriefcaseAccountMiniForm,
    BriefcaseDocumentMiniForm,
    BriefcaseNoteMiniForm,
)


class StaffMemberDetailsView(
    UserPassesTestMixin, BWLoginRequiredMixin, SuccessMessageMixin, DetailView
):
    """View rendering comprehensive staff member details for managers."""

    template_name = "beach_wood_user/details.html"
    model = BWUser
    http_method_names: ClassVar[list[str]] = ["get"]
    permission_denied_message = _("You do not have permission to access this page.")

    def test_func(self) -> bool:
        """Verify requesting user is authorized to view staff details."""
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return (
            user.user_type == CON_MANAGER
            or (
                user.user_type == CON_ASSISTANT
                and user.has_perm(ASSISTANT_FULL_MANAGER_PERMISSION_WITH_MODEL_NAME)
            )
            or user.has_perm("beach_wood_user.developer_user")
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Populate template context with staff details, forms, and assignments."""
        context = super().get_context_data(**kwargs)
        context.setdefault(
            "title", f"{self.object.fullname} - " + self.object.user_type.title()
        )
        clients = ClientProxy.objects.order_by("name")
        permissions_form = BWPermissionsForm(
            staff_user=self.get_object(), initial={"user": self.get_object().pk}
        )
        special_assignment_form = MiniSpecialAssignmentForm(
            renderer=BWFormRenderer(),
            initial={
                "assigned_by": self.request.user.pk,
                "client": self.get_object().pk,
            },
        )
        staff_form = None
        staff_form_initial = self.get_object().get_staff_details()
        removed_fields = ["password", "profile_picture", "confirm_password"]
        if self.get_object().user_type == CON_BOOKKEEPER:
            staff_form = BookkeeperForm(
                initial=staff_form_initial, removed_fields=removed_fields
            )
        elif self.get_object().user_type == CON_ASSISTANT:
            staff_form = AssistantForm(
                initial=staff_form_initial, removed_fields=removed_fields
            )
        elif self.get_object().user_type == CON_MANAGER:
            staff_form = ManagerForm(
                initial=staff_form_initial, removed_fields=removed_fields
            )
        briefcase_note_form = BriefcaseNoteMiniForm(
            initial={"briefcase": self.get_object().briefcase.pk}
        )
        briefcase_document_form = BriefcaseDocumentMiniForm(
            initial={"briefcase": self.get_object().briefcase.pk}
        )
        briefcase_account_form = BriefcaseAccountMiniForm(
            initial={"briefcase": self.get_object().briefcase.pk}
        )

        context.setdefault("clients", clients)
        context.setdefault("special_assignment_form", special_assignment_form)
        context.setdefault("staff_form", staff_form)
        context.setdefault("permissions_form", permissions_form)
        context.setdefault("briefcase_note_form", briefcase_note_form)
        context.setdefault("briefcase_document_form", briefcase_document_form)
        context.setdefault("briefcase_account_form", briefcase_account_form)
        return context


class StaffProfileView(
    UserPassesTestMixin,
    BWLoginRequiredMixin,
    SuccessMessageMixin,
    FormView,
    DetailView,
):
    """View rendering and processing profile updates for authorized users."""

    template_name = "beach_wood_user/profile.html"
    model = BWUser
    http_method_names: ClassVar[list[str]] = ["get", "post"]
    permission_denied_message = _("You do not have permission to access this page.")
    form_class = ProfileForm
    success_message = _("Profile updated successfully!")

    def test_func(self) -> bool:
        """Verify user is owner or manager."""
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        target_user = self.get_object()
        if user.pk == target_user.pk:
            return True
        return (
            user.user_type == CON_MANAGER
            or (
                user.user_type == CON_ASSISTANT
                and user.has_perm(ASSISTANT_FULL_MANAGER_PERMISSION_WITH_MODEL_NAME)
            )
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Populate profile view context."""
        context = super().get_context_data(**kwargs)
        context.setdefault("title", f"{self.object.fullname}")
        return context

    def get_success_url(self) -> str:
        """Return redirect URL upon successful profile update."""
        success_url = reverse_lazy(
            "dashboard:staff:staff-profile", kwargs={"pk": self.object.pk}
        )
        return str(success_url)

    def get_form_kwargs(self) -> dict[str, Any]:
        """Inject target profile instance and form submission data."""
        kwargs = {
            "initial": self.get_initial(),
            "prefix": self.get_prefix(),
        }
        kwargs.update(
            {
                "instance": self.get_object()
                .get_staff_member_object.get("staff_object")
                .profile
            }
        )
        if self.request.method in ("POST", "PUT"):
            kwargs.update(
                {
                    "data": self.request.POST,
                    "files": self.request.FILES,
                }
            )
        return kwargs

    def form_valid(self, form: ProfileForm) -> HttpResponse:
        """Save updated profile upon valid form submission."""
        form.save()
        self.object = self.get_object()
        return super().form_valid(form)

    def form_invalid(self, form: ProfileForm) -> HttpResponse:
        """Render invalid form response."""
        self.object = self.get_object()
        return self.render_to_response(self.get_context_data(form=form))


class StaffUpdatePasswordView(
    UserPassesTestMixin,
    ThrottledViewMixin,
    BWLoginRequiredMixin,
    SuccessMessageMixin,
    SingleObjectMixin,
    FormView,
):
    """View rendering and processing password updates for authorized users."""

    throttle_classes: ClassVar[list[type[AuthEndpointRateThrottle]]] = [
        AuthEndpointRateThrottle
    ]
    form_class = ForceChangePasswordForm
    template_name = "beach_wood_user/update_password.html"
    model = BWUser
    http_method_names: ClassVar[list[str]] = ["get", "post"]
    context_object_name = "object"
    permission_denied_message = _("You do not have permission to access this page.")
    success_message = _("Password updated successfully!")

    def test_func(self) -> bool:
        """Verify user is owner or manager."""
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        target_user = self.get_object()
        if user.pk == target_user.pk:
            return True
        return (
            user.user_type == CON_MANAGER
            or (
                user.user_type == CON_ASSISTANT
                and user.has_perm(ASSISTANT_FULL_MANAGER_PERMISSION_WITH_MODEL_NAME)
            )
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Populate password update context."""
        context = super().get_context_data(**kwargs)
        context.setdefault(
            "title", _(f"Force update password - {self.get_object().fullname}")
        )
        return context

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Render password form for GET request."""
        self.object = self.get_object()
        return self.render_to_response(self.get_context_data())

    def form_invalid(self, form: BaseForm) -> HttpResponse:
        """Render invalid form response."""
        self.object = self.get_object()
        return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form: ForceChangePasswordForm) -> HttpResponse:
        """Set new password on target user and save."""
        self.object = self.get_object()
        self.object.set_password(form.cleaned_data["password1"])
        self.object.save(update_fields=["password"])
        if self.request.user.pk == self.object.pk:
            update_session_auth_hash(self.request, self.object)
        return super().form_valid(form)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Process form submission for POST request."""
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def get_success_url(self) -> str:
        """Return redirect URL upon successful password update."""
        success_url = reverse_lazy(
            "dashboard:staff:staff-update-password", kwargs={"pk": self.get_object().pk}
        )
        return str(success_url)


