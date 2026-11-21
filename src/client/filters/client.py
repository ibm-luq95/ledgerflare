"""Client filtering module for dashboard client views."""

from __future__ import annotations

from typing import ClassVar

import django_filters
from django import forms
from django.utils.translation import gettext as _

from bookkeeper.models import BookkeeperProxy
from cfo.models.proxy import CFOProxy
from client.models import ClientProxy
from client_category.models import ClientCategory
from core.choices import ClientStatusEnum, ImportantContactLabelsEnum
from core.filters.filter_created_mixin import FilterCreatedMixin


_INPUT_CSS = (
    "py-2 px-3 block w-full border-gray-200 rounded-lg text-xs "
    "focus:border-blue-500 focus:ring-blue-500 dark:bg-neutral-800 "
    "dark:border-neutral-700 dark:text-neutral-300"
)


class ClientFilter(FilterCreatedMixin):
    """FilterSet for ClientProxy list views with extended filter fields."""

    form_prefix = "client-filter"

    name = django_filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
        label=_("Client Name"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Filter by client name..."),
                "class": _INPUT_CSS,
            }
        ),
    )
    industry = django_filters.CharFilter(
        field_name="industry",
        lookup_expr="icontains",
        label=_("Industry"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Filter by industry..."),
                "class": _INPUT_CSS,
            }
        ),
    )
    status = django_filters.ChoiceFilter(
        field_name="status",
        choices=ClientStatusEnum.choices,
        label=_("Status"),
        empty_label=_("All Statuses"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    bookkeepers = django_filters.ModelChoiceFilter(
        field_name="bookkeepers",
        queryset=BookkeeperProxy.objects.select_related("user"),
        label=_("Managed By (Bookkeeper)"),
        empty_label=_("All Bookkeepers"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    cfos = django_filters.ModelChoiceFilter(
        field_name="cfos",
        queryset=CFOProxy.objects.select_related("user"),
        label=_("CFO"),
        empty_label=_("All CFOs"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    categories = django_filters.ModelChoiceFilter(
        field_name="categories",
        queryset=ClientCategory.objects.all(),
        label=_("Category"),
        empty_label=_("All Categories"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    city = django_filters.CharFilter(
        field_name="city",
        lookup_expr="icontains",
        label=_("City"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("City..."),
                "class": _INPUT_CSS,
            }
        ),
    )
    state = django_filters.CharFilter(
        field_name="state",
        lookup_expr="icontains",
        label=_("State"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("State..."),
                "class": _INPUT_CSS,
            }
        ),
    )
    contact_name = django_filters.CharFilter(
        field_name="important_contacts__company_name",
        lookup_expr="icontains",
        label=_("Contact Name / Company"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Contact company..."),
                "class": _INPUT_CSS,
            }
        ),
    )
    contact_label = django_filters.ChoiceFilter(
        field_name="important_contacts__contact_label",
        label=_("Contact Label"),
        choices=ImportantContactLabelsEnum.choices,
        empty_label=_("All Contact Labels"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )

    class Meta:
        """FilterSet metadata configuration."""

        model = ClientProxy
        fields: ClassVar[list[str]] = [
            "name",
            "industry",
            "status",
            "bookkeepers",
            "cfos",
            "categories",
            "city",
            "state",
            "contact_name",
            "contact_label",
        ]
