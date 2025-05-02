# -*- coding: utf-8 -*-#

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import DeleteView, ListView, FormView
from django.views.generic.detail import SingleObjectMixin

from assistant.filters import AssistantFilter
from assistant.forms import AssistantForm
from assistant.models import AssistantProxy
from beach_wood_user.models import BWUser
from core.cache import BWSiteSettingsViewMixin
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.utils.developments.debugging_print_object import DebuggingPrint
from core.views.mixins import BWBaseListViewMixin, BWLoginRequiredMixin


class AssistantListView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    ListView,
):
    permission_required = "assistant.can_view_list"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "core/crudl/list.html"
    model = AssistantProxy
    paginate_by = LIST_VIEW_PAGINATE_BY
    list_type = "list"
    is_show_create_btn = True
    is_filters_enabled = True
    is_actions_menu_enabled = True
    is_header_enabled = True
    is_footer_enabled = True
    show_info_icon = True
    page_title = _("Assistants")
    page_header = _("Assistants".title())
    component_path = "bw_components/assistant/table_list.html"
    actions_base_url = "dashboard:management_assistant"
    filter_cancel_url = "dashboard:management_assistant:list"
    table_header_title = _("C")
    pagination_list_url_name = "dashboard:management_assistant:list"
    actions_items = "update,delete"
    base_url_name = "dashboard:management_assistant"
    empty_label = _("assistants")
    subtitle = _("assistants staff".title())

    # queryset = AssistantProxy.objects.get_queryset().order_by("-user__created_at")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # context.setdefault("filter_form", self.filterset.form)
        context.setdefault("extra_context", {})
        context.setdefault(
            "info_details",
            {
                "tooltip_txt": BW_INFO_MODAL_CSS_CLASSES.get("assistant").get(
                    "tooltip_txt"
                ),
                "modal_css_id": BW_INFO_MODAL_CSS_CLASSES.get("assistant").get("cssID"),
            },
        )
        context.setdefault("filter_form_id", "assistantsFilterForm")
        if self.request.GET:
            context["title"] = _("Filtered Assistants")
        else:
            context["title"] = _("Assistants")

        # debugging_print(self.filterset.form["name"])
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = AssistantFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs


class AssistantCreateView(
    PermissionRequiredMixin,
    SuccessMessageMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    FormView,
):
    # permission_required = ["assistant.add_assistant", "assistant.add_assistantproxy"]
    permission_required = "assistant.add_assistantproxy"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "assistant/create.html"
    form_class = AssistantForm
    success_message = _("Assistant created successfully")
    success_url = reverse_lazy("dashboard:management_assistant:list")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Create a new assistant"))
        return context

    def form_valid(self, form: AssistantForm):
        """If the form is valid, save the associated model."""
        try:
            with transaction.atomic():
                # DebuggingPrint.pprint(form.cleaned_data)
                # raise Exception
                user_details = {
                    "first_name": form.cleaned_data.get("first_name"),
                    "last_name": form.cleaned_data.get("last_name"),
                    "email": form.cleaned_data.get("email"),
                    "user_type": form.STAFF_MEMBER_TYPE,
                    "password": form.cleaned_data.get("password"),
                }
                profile_details = {
                    "linkedin": form.cleaned_data.get("linkedin"),
                    "instagram": form.cleaned_data.get("instagram"),
                    "github": form.cleaned_data.get("github"),
                    "facebook": form.cleaned_data.get("facebook"),
                    "twitter": form.cleaned_data.get("twitter"),
                    "address": form.cleaned_data.get("address"),
                    "phone_number": form.cleaned_data.get("phone_number"),
                    "bio": form.cleaned_data.get("bio"),
                    "profile_picture": form.cleaned_data.get("profile_picture"),
                }
                # new_user = BWUser.objects.create(**user_details)
                new_user = BWUser.objects.create_user(**user_details)
                # new_user.set_password(form.cleaned_data.get("password"))
                new_user.assistant.assistant_type = form.cleaned_data.get("assistant_type")
                new_user.assistant.save()
                for attr, value in profile_details.items():
                    setattr(new_user.assistant.profile, attr, value)
                new_user.assistant.profile.save()
            return super().form_valid(form)
        except Exception as ex:
            raise Exception(str(ex))


class AssistantUpdateView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    SuccessMessageMixin,
    BWSiteSettingsViewMixin,
    SingleObjectMixin,
    FormView,
):
    # permission_required = ["assistant.change_assistant", "assistant.change_assistantproxy"]
    permission_required = "assistant.change_assistantproxy"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "assistant/update.html"
    form_class = AssistantForm
    # success_message = _("Bookkeeper updated successfully")
    # success_url = reverse_lazy("dashboard:management_assistant:list")
    model = AssistantProxy

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        self.object = self.get_object()  # this must be before super()
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Update assistant"))
        return context

    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return _(f"Assistant {self.object.user.fullname} updated successfully!")

    def get_object(self, queryset=None):
        """
        Retrieve the object that this view is displaying.
        """
        if queryset is None:
            queryset = self.get_queryset()
        # Retrieve the object

        return queryset.get(pk=self.kwargs["pk"])

    def get_success_url(self) -> str:
        """Return the URL to redirect to after processing a valid form."""
        success_url = reverse_lazy(
            "dashboard:management_assistant:update", kwargs={"pk": self.object.pk}
        )
        return str(success_url)  # success_url may be lazy

    def get_initial(self) -> dict:
        initial = super().get_initial()
        initial["email"] = self.object.user.email
        initial["first_name"] = self.object.user.first_name
        initial["last_name"] = self.object.user.last_name
        initial["bio"] = self.object.profile.bio
        initial["profile_picture"] = self.object.profile.profile_picture
        initial["assistant_type"] = self.object.assistant_type
        initial["address"] = self.object.profile.address
        initial["phone_number"] = self.object.profile.phone_number
        initial["facebook"] = self.object.profile.facebook
        initial["twitter"] = self.object.profile.twitter
        initial["github"] = self.object.profile.github
        initial["linkedin"] = self.object.profile.linkedin
        initial["instagram"] = self.object.profile.instagram

        return initial

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form: AssistantForm):
        """If the form is valid, save the associated model."""
        try:
            with transaction.atomic():
                assistant = self.object
                user_details = {
                    "first_name": form.cleaned_data.get("first_name"),
                    "last_name": form.cleaned_data.get("last_name"),
                    "email": form.cleaned_data.get("email"),
                    "user_type": form.STAFF_MEMBER_TYPE,
                }
                for key, value in user_details.items():
                    setattr(assistant.user, key, value)
                assistant.user.save()
                assistant.assistant_type = form.cleaned_data.get("assistant_type")
                assistant.save()
                profile_details = {
                    "linkedin": form.cleaned_data.get("linkedin"),
                    "instagram": form.cleaned_data.get("instagram"),
                    "github": form.cleaned_data.get("github"),
                    "facebook": form.cleaned_data.get("facebook"),
                    "twitter": form.cleaned_data.get("twitter"),
                    "address": form.cleaned_data.get("address"),
                    "phone_number": form.cleaned_data.get("phone_number"),
                    "bio": form.cleaned_data.get("bio"),
                    "profile_picture": form.cleaned_data.get("profile_picture"),
                }
                for attr, value in profile_details.items():
                    setattr(assistant.profile, attr, value)
                assistant.profile.save()
            return super().form_valid(form)
        except Exception as ex:
            raise Exception(str(ex))


class AssistantDeleteView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    DeleteView,
):
    # permission_required = ["assistant.delete_assistant", "assistant.delete_assistantproxy"]
    permission_required = "assistant.delete_assistantproxy"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "assistant/management/delete.html"
    model = AssistantProxy
    success_message = _("Assistant deleted successfully")
    success_url = reverse_lazy("dashboard:management_assistant:list")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Delete assistant"))
        context.setdefault("cancel_url", "dashboard:management_assistant:list")
        context.setdefault("object", self.get_object())
        context.setdefault("object_name", "assistant")
        context.setdefault("form_css_id", "assistantDeleteForm")
        return context

    def form_valid(self, form):
        success_url = self.get_success_url()
        user = BWUser.objects.get(pk=self.object.user.pk)
        user.delete()
        self.object.delete()
        return HttpResponseRedirect(success_url)
