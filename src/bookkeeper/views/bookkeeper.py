# -*- coding: utf-8 -*-#
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import DeleteView, ListView, FormView
from django.views.generic.detail import SingleObjectMixin

from beach_wood_user.models import BWUser
from bookkeeper.filters import BookkeeperFilter
from bookkeeper.forms import BookkeeperForm
from bookkeeper.models import BookkeeperProxy
from core.cache import BWSiteSettingsViewMixin
from core.constants import LIST_VIEW_PAGINATE_BY
from core.constants.css_classes import BW_INFO_MODAL_CSS_CLASSES
from core.utils import debugging_print
from core.utils.developments.debugging_print_object import DebuggingPrint
from core.views.mixins import BWBaseListViewMixin, BWLoginRequiredMixin


class BookkeeperListView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    BWBaseListViewMixin,
    ListView,
):
    permission_required = "bookkeeper.can_view_list"
    template_name = "core/crudl/list.html"
    model = BookkeeperProxy
    paginate_by = LIST_VIEW_PAGINATE_BY
    list_type = "list"
    is_show_create_btn = True
    is_filters_enabled = True
    is_actions_menu_enabled = True
    is_header_enabled = True
    is_footer_enabled = True
    show_info_icon = True
    page_title = _("Bookkeepers")
    page_header = _("Bookkeepers".title())
    component_path = "bw_components/bookkeeper/table_list.html"
    actions_base_url = "dashboard:management_bookkeeper"
    filter_cancel_url = "dashboard:management_bookkeeper:list"
    table_header_title = _("C")
    pagination_list_url_name = "dashboard:management_bookkeeper:list"
    actions_items = "update,delete"
    base_url_name = "dashboard:management_bookkeeper"
    empty_label = _("bookkeepers")
    subtitle = _("bookkeepers staff".title())

    # queryset = BookkeeperProxy.objects.get_queryset().order_by("-user__created_at")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # context.setdefault("filter_form", self.filterset.form)
        context.setdefault("extra_context", {})
        context.setdefault(
            "info_details",
            {
                "tooltip_txt": BW_INFO_MODAL_CSS_CLASSES.get("bookkeeper").get(
                    "tooltip_txt"
                ),
                "modal_css_id": BW_INFO_MODAL_CSS_CLASSES.get("bookkeeper").get("cssID"),
            },
        )
        context.setdefault("filter_form_id", "bookkeepersFilterForm")
        if self.request.GET:
            context["title"] = _("Filtered Bookkeepers")
        else:
            context["title"] = _("Bookkeepers")

        # debugging_print(self.filterset.form["name"])
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = BookkeeperFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs


class BookkeeperCreateView(
    PermissionRequiredMixin,
    SuccessMessageMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    FormView,
):
    # permission_required = ["bookkeeper.add_bookkeeper", "bookkeeper.add_bookkeeperproxy"]
    permission_required = "bookkeeper.add_bookkeeperproxy"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "bookkeeper/create.html"
    form_class = BookkeeperForm
    success_message = _("Bookkeeper created successfully")
    success_url = reverse_lazy("dashboard:management_bookkeeper:list")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _("Create a new bookkeeper"))
        return context

    def form_valid(self, form: BookkeeperForm):
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
            new_user.bookkeeper.profile_picture = form.cleaned_data.get("profile_picture")
            new_user.bookkeeper.bio = form.cleaned_data.get("bio")
            new_user.bookkeeper.save()
        return super().form_valid(form)


# def get_initial(self) -> dict[str, Any]:
#     return {"user_type": CON_BOOKKEEPER}


class BookkeeperUpdateView(
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
    permission_required = "bookkeeper.change_bookkeeperproxy"
    permission_denied_message = _("You do not have permission to access this page.")
    template_name = "bookkeeper/update.html"
    form_class = BookkeeperForm
    # success_message = _("Bookkeeper updated successfully")
    # success_url = reverse_lazy("dashboard:management_bookkeeper:list")
    model = BookkeeperProxy

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        self.object = self.get_object()  # this must be before super()
        context = super().get_context_data(**kwargs)
        context.setdefault("title", _(f"Update - {self.object.user.fullname}"))
        return context

    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return _(f"Bookkeeper {self.object.user.fullname} updated successfully!")

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
            "dashboard:management_bookkeeper:update", kwargs={"pk": self.object.pk}
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

    def form_valid(self, form: BookkeeperForm):
        """If the form is valid, save the associated model."""
        # debugging_print("Form valid")
        with transaction.atomic():
            bookkeeper = self.object

            user_details = {
                "first_name": form.cleaned_data.get("first_name"),
                "last_name": form.cleaned_data.get("last_name"),
                "email": form.cleaned_data.get("email"),
                "user_type": form.STAFF_MEMBER_TYPE,
            }
            for key, value in user_details.items():
                setattr(bookkeeper.user, key, value)
            password = form.cleaned_data.get("password")
            if password:
                bookkeeper.user.set_password(password)
            bookkeeper.user.save()
            bookkeeper.profile.profile_picture = form.cleaned_data.get("profile_picture")
            bookkeeper.profile.bio = form.cleaned_data.get("bio")
            bookkeeper.profile.address = form.cleaned_data.get("address")
            bookkeeper.profile.phone_number = form.cleaned_data.get("phone_number")
            bookkeeper.profile.facebook = form.cleaned_data.get("facebook")
            bookkeeper.profile.twitter = form.cleaned_data.get("twitter")
            bookkeeper.profile.linkedin = form.cleaned_data.get("linkedin")
            bookkeeper.profile.github = form.cleaned_data.get("github")
            bookkeeper.profile.instagram = form.cleaned_data.get("instagram")

            bookkeeper.profile.save()
            bookkeeper.save()
        return super().form_valid(form)


class BookkeeperDeleteView(
    PermissionRequiredMixin,
    BWLoginRequiredMixin,
    BWSiteSettingsViewMixin,
    SuccessMessageMixin,
    DeleteView,
):
    template_name = "bookkeeper/management/delete.html"
    model = BookkeeperProxy
    success_message = _("Bookkeeper deleted successfully")
    success_url = reverse_lazy("dashboard:management_bookkeeper:list")
    permission_denied_message = _("You do not have permission to access this page.")
    # permission_required = [
    #     "bookkeeper.delete_bookkeeper",
    #     "bookkeeper.delete_bookkeeperproxy",
    # ]
    permission_required = "bookkeeper.delete_bookkeeperproxy"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # raise Exception("dd")
        context.setdefault("title", _("Delete bookkeeper"))
        context.setdefault("cancel_url", "dashboard:management_bookkeeper:list")
        context.setdefault("object", self.get_object())
        context.setdefault("object_name", "bookkeeper")
        context.setdefault("form_css_id", "bookkeeperDeleteForm")
        bookkeeper: BookkeeperProxy = self.get_object()
        user = bookkeeper.user
        context.setdefault("assigned_assignments", user.assigned_assignments.all())
        jobs = bookkeeper.get_user_jobs()
        context.setdefault("clients", bookkeeper.clients.all())
        context.setdefault("user_jobs", jobs)
        return context

    #
    def form_valid(self, form):
        success_url = self.get_success_url()
        user = BWUser.objects.get(pk=self.object.user.pk)
        user.delete()
        self.object.delete()
        return HttpResponseRedirect(success_url)
