from __future__ import annotations

from typing import ClassVar

import django_filters
from django import forms
from django.utils.translation import gettext as _

from client.models import ClientProxy
from core.choices import ImportantContactLabelsEnum
from core.choices.filters import DateFiltersEnum
from core.filters.filter_created_mixin import FilterCreatedMixin
from important_contact.models import ImportantContactProxy


_INPUT_CSS = (
    "py-2 px-3 block w-full border-gray-200 rounded-lg text-xs "
    "focus:border-blue-500 focus:ring-blue-500 dark:bg-neutral-800 "
    "dark:border-neutral-700 dark:text-neutral-200"
)


class ImportantContactFilter(FilterCreatedMixin):
    """FilterSet for ImportantContactProxy list views with extended filter fields."""

    contact_first_name = django_filters.CharFilter(
        field_name="contact_first_name",
        lookup_expr="icontains",
        label=_("First Name"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Filter by first name..."),
                "class": _INPUT_CSS,
            }
        ),
    )
    contact_last_name = django_filters.CharFilter(
        field_name="contact_last_name",
        lookup_expr="icontains",
        label=_("Last Name"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Filter by last name..."),
                "class": _INPUT_CSS,
            }
        ),
    )
    company_name = django_filters.CharFilter(
        field_name="company_name",
        lookup_expr="icontains",
        label=_("Company Name"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Filter by company..."),
                "class": _INPUT_CSS,
            }
        ),
    )
    contact_email = django_filters.CharFilter(
        field_name="contact_email",
        lookup_expr="icontains",
        label=_("Email"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Filter by email..."),
                "class": _INPUT_CSS,
            }
        ),
    )
    contact_phone = django_filters.CharFilter(
        field_name="contact_phone",
        lookup_expr="icontains",
        label=_("Phone"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Filter by phone..."),
                "class": _INPUT_CSS,
            }
        ),
    )
    contact_city = django_filters.CharFilter(
        field_name="contact_city",
        lookup_expr="icontains",
        label=_("City"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Filter by city..."),
                "class": _INPUT_CSS,
            }
        ),
    )
    contact_label = django_filters.ChoiceFilter(
        field_name="contact_label",
        choices=ImportantContactLabelsEnum.choices,
        label=_("Role / Label"),
        empty_label=_("All Roles"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    client = django_filters.ModelChoiceFilter(
        field_name="client",
        queryset=ClientProxy.objects.only("id", "name").order_by("name"),
        label=_("Client"),
        empty_label=_("All Clients"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    created = django_filters.ChoiceFilter(
        field_name="created_at",
        choices=DateFiltersEnum.choices,
        method="filter_created",
        label=_("Created Timeframe"),
        empty_label=_("All Dates"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    created_between = django_filters.DateFromToRangeFilter(
        field_name="created_at",
        widget=django_filters.widgets.DateRangeWidget(
            attrs={
                "placeholder": "YYYY-MM-DD",
                "type": "date",
                "class": _INPUT_CSS,
            }
        ),
        label=_("Created Between"),
    )

    class Meta:
        model = ImportantContactProxy
        fields: ClassVar[list[str]] = [
            "contact_first_name",
            "contact_last_name",
            "company_name",
            "contact_email",
            "contact_phone",
            "contact_city",
            "contact_label",
            "client",
            "created",
            "created_between",
        ]
