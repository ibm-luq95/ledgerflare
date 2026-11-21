"""Job filtering module for dashboard job views."""

from __future__ import annotations

import django_filters
from django import forms
from django.utils.translation import gettext as _

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from core.choices import (
    JobStateEnum,
    JobStatusEnum,
    JobTypeEnum,
)
from core.choices.fiscal_year import FiscalYearEnum
from core.choices.months import MonthChoices
from core.filters.filter_created_mixin import FilterCreatedMixin
from job.models import JobProxy
from job_category.models import JobCategory

_INPUT_CSS = (
    "py-2 px-3 block w-full border-gray-200 rounded-lg text-xs "
    "focus:border-blue-500 focus:ring-blue-500 dark:bg-neutral-800 "
    "dark:border-neutral-700 dark:text-neutral-300"
)


class JobFilter(FilterCreatedMixin):
    """FilterSet for JobProxy list views with extended filter fields."""

    form_prefix = "job-filter"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form.fields.pop("created_between", None)

    title = django_filters.CharFilter(
        field_name="title",
        lookup_expr="icontains",
        label=_("Job Title"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Filter by job title..."),
                "class": _INPUT_CSS,
            }
        ),
    )
    client = django_filters.ModelChoiceFilter(
        field_name="client",
        queryset=ClientProxy.objects.all(),
        label=_("Client"),
        empty_label=_("All Clients"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    managed_by = django_filters.ModelChoiceFilter(
        field_name="managed_by",
        queryset=BWUser.objects.filter(is_active=True),
        label=_("Managed By"),
        empty_label=_("All Staff"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    status = django_filters.ChoiceFilter(
        field_name="status",
        choices=JobStatusEnum.choices,
        label=_("Status"),
        empty_label=_("All Statuses"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    state = django_filters.ChoiceFilter(
        field_name="state",
        choices=JobStateEnum.choices,
        label=_("State"),
        empty_label=_("All States"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    job_type = django_filters.ChoiceFilter(
        field_name="job_type",
        choices=JobTypeEnum.choices,
        label=_("Job Type"),
        empty_label=_("All Job Types"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    period_year = django_filters.ChoiceFilter(
        field_name="period_year",
        choices=FiscalYearEnum.choices,
        label=_("Period Year"),
        empty_label=_("All Years"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    period_month = django_filters.ChoiceFilter(
        field_name="period_month",
        choices=MonthChoices.choices,
        label=_("Period Month"),
        empty_label=_("All Months"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    due_date = django_filters.DateFilter(
        field_name="due_date",
        label=_("Due Date"),
        widget=forms.DateInput(attrs={"type": "date", "class": _INPUT_CSS}),
    )
    due_date__gt = django_filters.DateFilter(
        field_name="due_date",
        label=_("Due After"),
        widget=forms.DateInput(attrs={"type": "date", "class": _INPUT_CSS}),
        lookup_expr="gt",
    )
    due_date__lt = django_filters.DateFilter(
        field_name="due_date",
        label=_("Due Before"),
        widget=forms.DateInput(attrs={"type": "date", "class": _INPUT_CSS}),
        lookup_expr="lt",
    )
    categories = django_filters.ModelMultipleChoiceFilter(
        field_name="categories",
        queryset=JobCategory.objects.all(),
        label=_("Categories"),
        widget=forms.SelectMultiple(
            attrs={"data_name": "job-categories", "class": _INPUT_CSS}
        ),
        lookup_expr="exact",
    )

    class Meta:
        model = JobProxy
        fields = [
            "title",
            "client",
            "managed_by",
            "status",
            "state",
            "job_type",
            "period_year",
            "period_month",
            "due_date",
            "due_date__gt",
            "due_date__lt",
            "categories",
        ]
