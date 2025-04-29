# -*- coding: utf-8 -*-#
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import DeleteView, ListView, FormView
from django.views.generic.detail import SingleObjectMixin

from beach_wood_user.models import BWUser
from bookkeeper.models import BookkeeperProxy
from cfo.filters.cfo import CFOFilter
from cfo.forms.cfo import CFOForm
from cfo.models import CFOProxy
from core.cache import BWSiteSettingsViewMixin
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.utils import debugging_print
from core.utils.developments.debugging_print_object import DebuggingPrint
from core.views.mixins import BWBaseListViewMixin, BWLoginRequiredMixin


class CFOListView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    ListView,
):
    permission_required = "cfo.can_view_list"
    template_name = "core/crudl/list.html"
    model = CFOProxy
    paginate_by = LIST_VIEW_PAGINATE_BY
    list_type = "list"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context["title"] = _("CFOs")
        context.setdefault("filter_form", self.filterset.form)
        context.setdefault("list_type", self.list_type)
        context.setdefault("page_header", _("CFOs"))
        context.setdefault("component_path", "bw_components/cfo/table_list.html")
        context.setdefault("subtitle", _("CFOs staff"))
        context.setdefault("actions_base_url", "dashboard:management_cfo")
        context.setdefault("filter_cancel_url", "dashboard:management_cfo:list")
        context.setdefault("table_header_title", _("C"))
        context.setdefault("table_header_subtitle", _("management_bookkeeper subtitle"))
        context.setdefault("is_show_create_btn", True)
        context.setdefault("pagination_list_url_name", "dashboard:management_cfo:list")
        context.setdefault("is_filters_enabled", True)
        context.setdefault("is_actions_menu_enabled", True)
        context.setdefault("is_header_enabled", True)
        context.setdefault("is_footer_enabled", True)
        context.setdefault("actions_items", "update,delete")
        context.setdefault("base_url_name", "dashboard:management_cfo")
        context.setdefault("empty_label", _("CFOs"))
        context.setdefault("extra_context", {})
        context.setdefault("show_info_icon", True)
        context.setdefault(
            "info_details",
            {
                "tooltip_txt": BW_INFO_MODAL_CSS_CLASSES.get("cfo").get("tooltip_txt"),
                "modal_css_id": BW_INFO_MODAL_CSS_CLASSES.get("cfo").get("cssID"),
            },
        )
        context.setdefault("filter_form_id", "cfosFilterForm")
        if self.request.GET:
            context["title"] = _("Filtered CFOs")
        else:
            context["title"] = _("CFOs")

        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = CFOFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs


class CFOCreateView(
    PermissionRequiredMixin,
    SuccessMessageMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    FormView,
):
    permission_required = "cfo.add_cfoproxy"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "cfo/create.html"
    form_class = CFOForm
    success_message = _("CFO created successfully")
    success_url = reverse_lazy("dashboard:management_cfo:list")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Create a new CFO"))
        return context

    def form_valid(self, form: CFOForm):
        """If the form is valid, save the associated model."""
        with transaction.atomic():
            user_details = {
                "first_name": form.cleaned_data.get("first_name"),
                "last_name": form.cleaned_data.get("last_name"),
                "email": form.cleaned_data.get("email"),
                "user_type": form.STAFF_MEMBER_TYPE,
            }
            new_user = BWUser.objects.create(**user_details)
            debugging_print(form.cleaned_data.get("password"))
            new_user.set_password(form.cleaned_data.get("password"))
            new_user.save()
            new_user.cfo.profile_picture = form.cleaned_data.get("profile_picture")
            new_user.cfo.bio = form.cleaned_data.get("bio")
            new_user.cfo.save()
        return super().form_valid(form)


class CFOUpdateView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    SuccessMessageMixin,
    BWSiteSettingsViewMixin,
    SingleObjectMixin,
    FormView,
):
    # permission_required = [
    #     "bookkeeper.change_bookkeeper",
    #     "bookkeeper.change_bookkeeperproxy",
    # ]
    permission_required = "cfo.change_cfoproxy"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "cfo/update.html"
    form_class = CFOForm
    model = CFOProxy

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        self.object = self.get_object()  # this must be before super()
        context = super().get_context_data(**kwargs)
        DebuggingPrint.print(self.object.profile)
        context.setdefault("title", _(f"Update - {self.object.user.fullname}"))
        return context

    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return _(f"CFO {self.object.user.fullname} updated successfully!")

    def get_object(self, queryset=None):
        """
        Retrieve the object that this view is displaying.
        """
        if queryset is None:
            queryset = self.get_queryset()
        # Retrieve the object

        return queryset.get(pk=self.kwargs["pk"])

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        success_url = reverse_lazy(
            "dashboard:management_cfo:update", kwargs={"pk": self.object.pk}
        )
        return str(success_url)  # success_url may be lazy

    def get_initial(self) -> dict:
        initial = super().get_initial()
        initial["email"] = self.object.user.email
        initial["first_name"] = self.object.user.first_name
        initial["last_name"] = self.object.user.last_name
        initial["bio"] = self.object.profile.bio
        initial["address"] = self.object.profile.address
        initial["phone_number"] = self.object.profile.phone_number
        initial["facebook"] = self.object.profile.facebook
        initial["twitter"] = self.object.profile.twitter
        initial["linkedin"] = self.object.profile.linkedin
        initial["github"] = self.object.profile.github
        initial["instagram"] = self.object.profile.instagram
        initial["profile_picture"] = self.object.profile.profile_picture
        return initial

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            # form.split_user_profiles_inputs(excluded_fields=["password", "confirm_password"])
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form: CFOForm):
        """If the form is valid, save the associated model."""
        # debugging_print("Form valid")
        with transaction.atomic():
            cfo = self.object

            user_details = {
                "first_name": form.cleaned_data.get("first_name"),
                "last_name": form.cleaned_data.get("last_name"),
                "email": form.cleaned_data.get("email"),
                "user_type": form.STAFF_MEMBER_TYPE,
            }
            for key, value in user_details.items():
                setattr(cfo.user, key, value)
            password = form.cleaned_data.get("password")
            if password:
                cfo.user.set_password(password)
            cfo.user.save()
            cfo.profile.profile_picture = form.cleaned_data.get("profile_picture")
            cfo.profile.bio = form.cleaned_data.get("bio")
            cfo.profile.address = form.cleaned_data.get("address")
            cfo.profile.phone_number = form.cleaned_data.get("phone_number")
            cfo.profile.facebook = form.cleaned_data.get("facebook")
            cfo.profile.twitter = form.cleaned_data.get("twitter")
            cfo.profile.linkedin = form.cleaned_data.get("linkedin")
            cfo.profile.github = form.cleaned_data.get("github")
            cfo.profile.instagram = form.cleaned_data.get("instagram")

            cfo.profile.save()
            cfo.save()
        return super().form_valid(form)


class CFODeleteView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    DeleteView,
):
    template_name = "core/crudl/delete.html"
    model = CFOProxy
    success_message = _("CFO deleted successfully")
    success_url = reverse_lazy("dashboard:management_cfo:list")
    permission_denied_message = _("You do not have permission to access this page.")

    permission_required = "cfo.delete_cfoproxy"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Delete CFO"))
        context.setdefault("cancel_url", "dashboard:management_cfo:list")
        context.setdefault("object", self.get_object())
        context.setdefault("object_name", "cfo")
        context.setdefault("form_css_id", "cfoDeleteForm")
        return context

    def form_valid(self, form):
        success_url = self.get_success_url()
        user = BWUser.objects.get(pk=self.object.user.pk)
        user.delete()
        self.object.delete()
        return HttpResponseRedirect(success_url)
