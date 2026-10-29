from __future__ import annotations

from typing import ClassVar

import django_filters
from django import forms
from django.utils.translation import gettext as _

from client.models import ClientProxy
from core.choices import NoteSectionEnum
from core.choices.filters import DateFiltersEnum
from core.filters.filter_created_mixin import FilterCreatedMixin
from core.utils.text_search import search_in_text
from job.models import JobProxy
from note.models import NoteProxy
from task.models import TaskProxy


_INPUT_CSS = (
    "py-2 px-3 block w-full border-gray-200 rounded-lg text-xs "
    "focus:border-blue-500 focus:ring-blue-500 dark:bg-neutral-800 "
    "dark:border-neutral-700 dark:text-neutral-200"
)


class NoteFilter(FilterCreatedMixin):
    """FilterSet for NoteProxy list views with extended filter fields."""

    title = django_filters.CharFilter(
        field_name="title",
        lookup_expr="icontains",
        label=_("Note Title"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Filter by title..."),
                "class": _INPUT_CSS,
            }
        ),
    )
    body = django_filters.CharFilter(
        method="filter_body",
        label=_("Note Content"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Search note content..."),
                "class": _INPUT_CSS,
            }
        ),
    )

    def filter_body(self, queryset, name, value):
        """Filter notes using normalized in-memory search for encrypted body."""
        if not value:
            return queryset
        candidates = list(queryset)
        matching_pks = [
            obj.pk
            for obj in candidates
            if search_in_text(value, getattr(obj, "body", "") or "")
        ]
        return queryset.filter(pk__in=matching_pks)

    note_section = django_filters.ChoiceFilter(
        field_name="note_section",
        choices=NoteSectionEnum.choices,
        label=_("Section"),
        empty_label=_("All Sections"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    client = django_filters.ModelChoiceFilter(
        field_name="client",
        queryset=ClientProxy.objects.only("id", "name").order_by("name"),
        label=_("Client"),
        empty_label=_("All Clients"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    job = django_filters.ModelChoiceFilter(
        field_name="job",
        queryset=JobProxy.objects.only("id", "title").order_by("title"),
        label=_("Job"),
        empty_label=_("All Jobs"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    task = django_filters.ModelChoiceFilter(
        field_name="task",
        queryset=TaskProxy.objects.only("id", "title").order_by("title"),
        label=_("Task"),
        empty_label=_("All Tasks"),
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
        model = NoteProxy
        fields: ClassVar[list[str]] = [
            "title",
            "body",
            "note_section",
            "client",
            "job",
            "task",
            "created",
            "created_between",
        ]
