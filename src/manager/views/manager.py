# -*- coding: utf-8 -*-#
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    RedirectView,
    FormView,
)
from django.utils.translation import gettext as _
from django.views.generic.detail import SingleObjectMixin

from beach_wood_user.models import BWUser
from core.cache import BWSiteSettingsViewMixin
from core.choices import JobStateEnum, JobStatusEnum
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.utils.developments.utils import get_list_from_text_choices
from core.views.mixins import (
    BWLoginRequiredMixin,
    BWBaseListViewMixin,
    BWManagerAccessMixin,
)
from manager.filters import ManagerFilter
from manager.forms import ManagerForm
from manager.models import ManagerProxy


class ManagerListView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    ListView,
):
    # permission_required = ["manager.can_view_list", "manager.manager_user"]
    permission_required = "manager.can_view_list"
    template_name = "core/crudl/list.html"
    model = ManagerProxy
    paginate_by = LIST_VIEW_PAGINATE_BY
    list_type = "list"
    is_show_create_btn = True
    is_filters_enabled = True
    is_actions_menu_enabled = True
    is_header_enabled = True
    is_footer_enabled = True
    show_info_icon = False
    page_title = _("Managers")
    page_header = _("Managers".title())
    component_path = "bw_components/manager/table_list.html"
    actions_base_url = "dashboard:managers"
    filter_cancel_url = "dashboard:managers:list"
    table_header_title = _("C")
    pagination_list_url_name = "dashboard:managers:list"
    actions_items = "update,delete"
    base_url_name = "dashboard:managers"
    empty_label = _("managers")
    subtitle = _("managers".title())

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context["title"] = _("Managers")
        # context.setdefault("filter_form", self.filterset.form)
        # context.setdefault("list_type", self.list_type)
        context.setdefault("table_header_subtitle", _("managers subtitle"))
        context.setdefault("extra_context", {})
        context.setdefault(
            "info_details",
            {
                "tooltip_txt": BW_INFO_MODAL_CSS_CLASSES.get("manager").get("tooltip_txt"),
                "modal_css_id": BW_INFO_MODAL_CSS_CLASSES.get("manager").get("cssID"),
            },
        )
        context.setdefault("filter_form_id", "managerFilterForm")
        if self.request.GET:
            context["title"] = _("Filtered Managers")
        else:
            context["title"] = _("Managers")
        # debugging_print(self.filterset.form["name"])
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = ManagerFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs


class ManagerCreateView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    FormView,
):
    # permission_required = [
    #     "manager.add_managerproxy",
    #     "manager.add_manager",
    #     "manager.manager_user",
    # ]
    permission_required = "manager.add_managerproxy"
    template_name = "manager/create.html"
    form_class = ManagerForm
    success_message = _("Manager created successfully")
    success_url = reverse_lazy("dashboard:managers:list")

    # template_name_suffix =

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Create manager"))
        messages.info(self.request, _(f"Creating new manager, be careful"))
        return context

    def form_valid(self, form: ManagerForm):
        """If the form is valid, save the associated model."""
        try:
            with transaction.atomic():
                user_details = {
                    "first_name": form.cleaned_data.get("first_name"),
                    "last_name": form.cleaned_data.get("last_name"),
                    "email": form.cleaned_data.get("email"),
                    "user_type": form.STAFF_MEMBER_TYPE,
                    "is_superuser": form.cleaned_data.get("is_superuser"),
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
                new_user = BWUser.objects.create(**user_details)
                new_user.set_password(form.cleaned_data.get("password"))
                new_user.save()
                new_user.manager.save()
                for attr, value in profile_details.items():
                    setattr(new_user.manager.profile, attr, value)
                new_user.manager.profile.save()
            return super().form_valid(form)
        except Exception as ex:
            raise Exception(str(ex))


class ManagerUpdateView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    SuccessMessageMixin,
    BWSiteSettingsViewMixin,
    SingleObjectMixin,
    FormView,
):
    # permission_required = [
    #     "manager.change_managerproxy",
    #     "manager.change_manager",
    #     "manager.manager_user",
    # ]
    permission_required = "manager.change_managerproxy"
    template_name = "manager/update.html"
    form_class = ManagerForm
    success_message = _("Manager updated successfully")
    success_url = reverse_lazy("dashboard:manager:list")
    model = ManagerProxy

    # template_name_suffix = "_create_client"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        self.object = self.get_object()  # this must be before super()
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Update manager"))
        return context

    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return _(f"Manager {self.object.user.fullname} updated successfully!")

    def get_success_url(self) -> str:
        """Return the URL to redirect to after processing a valid form."""
        success_url = reverse_lazy(
            "dashboard:managers:update", kwargs={"pk": self.object.pk}
        )
        return str(success_url)  # success_url may be lazy

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

    def get_initial(self) -> dict:
        initial = super().get_initial()
        initial["email"] = self.object.user.email
        initial["first_name"] = self.object.user.first_name
        initial["last_name"] = self.object.user.last_name
        initial["bio"] = self.object.profile.bio
        initial["profile_picture"] = self.object.profile.profile_picture
        initial["is_superuser"] = self.object.user.is_superuser
        initial["address"] = self.object.profile.address
        initial["phone_number"] = self.object.profile.phone_number
        initial["facebook"] = self.object.profile.facebook
        initial["twitter"] = self.object.profile.twitter
        initial["github"] = self.object.profile.github
        initial["linkedin"] = self.object.profile.linkedin
        initial["instagram"] = self.object.profile.instagram

        return initial

    def form_valid(self, form: ManagerForm):
        """If the form is valid, save the associated model."""
        try:
            with transaction.atomic():
                manager = self.object
                user_details = {
                    "first_name": form.cleaned_data.get("first_name"),
                    "last_name": form.cleaned_data.get("last_name"),
                    "email": form.cleaned_data.get("email"),
                    "user_type": form.STAFF_MEMBER_TYPE,
                    "is_superuser": form.cleaned_data.get("is_superuser"),
                }
                for key, value in user_details.items():
                    setattr(manager.user, key, value)
                manager.user.save()
                manager.save()
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
                    setattr(manager.profile, attr, value)
                manager.profile.save()
            return super().form_valid(form)
        except Exception as ex:
            raise Exception(str(ex))

    def get_object(self, queryset=None):
        """
        Retrieve the object that this view is displaying.
        """
        if queryset is None:
            queryset = self.get_queryset()
        # Retrieve the object

        return queryset.get(pk=self.kwargs["pk"])


class ManagerDeleteView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    DeleteView,
):
    # permission_required = [
    #     "manager.delete_manager",
    #     "manager.delete_managerproxy",
    #     "manager.manager_user",
    # ]
    permission_required = "manager.delete_managerproxy"
    template_name = "core/crudl/delete.html"
    model = ManagerProxy
    success_message = _("Manager deleted successfully")
    success_url = reverse_lazy("dashboard:manager:list")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Delete manager"))
        context.setdefault("cancel_url", "dashboard:manager:list")
        context.setdefault("object", self.get_object())
        context.setdefault("object_name", "manager")
        context.setdefault("form_css_id", "managerDeleteForm")
        return context

    def form_valid(self, form):
        success_url = self.get_success_url()
        user = BWUser.objects.get(pk=self.object.user.pk)
        user.delete()
        self.object.delete()
        return HttpResponseRedirect(success_url)
