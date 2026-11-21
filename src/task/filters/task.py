"""Task filtering module for dashboard task views."""

from __future__ import annotations

from typing import ClassVar

import django_filters
from django import forms
from django.utils.translation import gettext as _

from beach_wood_user.models import BWUser
from bookkeeper.models import BookkeeperProxy
from client.models import ClientProxy
from core.choices import TaskStatusEnum, TaskTypeEnum
from core.choices.filters import DateFiltersEnum
from core.filters.filter_created_mixin import FilterCreatedMixin
from core.utils.text_search import search_in_text
from job.models import JobProxy
from task.models import TaskProxy


_INPUT_CSS = (
    "py-2 px-3 block w-full border-gray-200 rounded-lg text-xs "
    "focus:border-blue-500 focus:ring-blue-500 dark:bg-neutral-800 "
    "dark:border-neutral-700 dark:text-neutral-300"
)


class TaskFilter(FilterCreatedMixin):
    """FilterSet for TaskProxy list views with extended filter fields."""

    title = django_filters.CharFilter(
        field_name="title",
        lookup_expr="icontains",
        label=_("Task Title"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Filter by task title..."),
                "class": _INPUT_CSS,
            }
        ),
    )
    hints = django_filters.CharFilter(
        method="filter_hints",
        label=_("Hints"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Filter by hints..."),
                "class": _INPUT_CSS,
            }
        ),
    )

    def filter_hints(self, queryset, name, value):
        """Filter tasks using normalized in-memory search for encrypted hints."""
        if not value:
            return queryset
        candidates = list(queryset)
        matching_pks = [
            obj.pk
            for obj in candidates
            if search_in_text(value, getattr(obj, "hints", "") or "")
        ]
        return queryset.filter(pk__in=matching_pks)

    task_type = django_filters.ChoiceFilter(
        field_name="task_type",
        choices=TaskTypeEnum.choices,
        label=_("Task Type"),
        empty_label=_("All Task Types"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    status = django_filters.ChoiceFilter(
        field_name="status",
        choices=TaskStatusEnum.choices,
        label=_("Status"),
        empty_label=_("All Statuses"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    is_completed = django_filters.BooleanFilter(
        field_name="is_completed",
        label=_("Is Completed"),
        widget=forms.Select(
            choices=[
                ("", _("All")),
                ("true", _("Completed")),
                ("false", _("Not Completed")),
            ],
            attrs={"class": _INPUT_CSS},
        ),
    )
    job = django_filters.ModelChoiceFilter(
        field_name="job",
        queryset=JobProxy.objects.only("id", "title").order_by("title"),
        label=_("Job"),
        empty_label=_("All Jobs"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    job__client = django_filters.ModelChoiceFilter(
        field_name="job__client",
        queryset=ClientProxy.objects.only("id", "name").order_by("name"),
        label=_("Client"),
        empty_label=_("All Clients"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    client = django_filters.ModelChoiceFilter(
        field_name="job__client",
        queryset=ClientProxy.objects.only("id", "name").order_by("name"),
        label=_("Client"),
        empty_label=_("All Clients"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    job__managed_by = django_filters.ModelChoiceFilter(
        field_name="job__managed_by",
        queryset=BWUser.objects
        .filter(is_active=True)
        .only("id", "first_name", "last_name", "email", "user_type")
        .order_by("first_name", "last_name"),
        label=_("Managed By"),
        empty_label=_("All Staff"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    managed_by = django_filters.ModelChoiceFilter(
        field_name="job__managed_by",
        queryset=BWUser.objects
        .filter(is_active=True)
        .only("id", "first_name", "last_name", "email", "user_type")
        .order_by("first_name", "last_name"),
        label=_("Managed By"),
        empty_label=_("All Staff"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    job__bookkeeper = django_filters.ModelChoiceFilter(
        field_name="job__client__bookkeepers",
        queryset=BookkeeperProxy.objects
        .select_related("user")
        .only("id", "user__id", "user__first_name", "user__last_name", "user__email")
        .order_by("user__first_name"),
        label=_("Bookkeeper"),
        empty_label=_("All Bookkeepers"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    bookkeeper = django_filters.ModelChoiceFilter(
        field_name="job__client__bookkeepers",
        queryset=BookkeeperProxy.objects
        .select_related("user")
        .only("id", "user__id", "user__first_name", "user__last_name", "user__email")
        .order_by("user__first_name"),
        label=_("Bookkeeper"),
        empty_label=_("All Bookkeepers"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    created = django_filters.ChoiceFilter(
        field_name="created_at",
        choices=DateFiltersEnum.choices,
        method="filter_created",
        label=_("Created"),
        empty_label=_("All Dates"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    created_between = django_filters.DateFromToRangeFilter(
        field_name="created_at",
        widget=django_filters.widgets.RangeWidget(
            attrs={
                "placeholder": "YYYY-MM-DD",
                "type": "date",
                "class": _INPUT_CSS,
            }
        ),
        label=_("Created between"),
    )

    class Meta:
        """FilterSet metadata configuration."""

        model = TaskProxy
        fields: ClassVar[list[str]] = [
            "title",
            "hints",
            "task_type",
            "status",
            "is_completed",
            "job",
            "job__client",
            "job__managed_by",
            "job__bookkeeper",
            "client",
            "managed_by",
            "bookkeeper",
            "created",
            "created_between",
        ]
