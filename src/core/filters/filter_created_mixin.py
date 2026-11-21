# -*- coding: utf-8 -*-#
from datetime import timedelta, datetime
from typing import Any, Optional

import django_filters
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext as _

from core.choices.filters import DateFiltersEnum
from core.filters.filter_help_text import HelpfulFilterSet


class FilterCreatedMixin(HelpfulFilterSet):
    """
    A mixin class for filtering by created date.

    This mixin class provides a `created` filter field and a `created_between` filter field
    for filtering by the `created_at` field of a model. The `created` filter allows filtering
    by specific dates (e.g., "today", "this_week", "this_month") and the `created_between`
    filter allows filtering by a range of dates.

    Attributes:
        created (django_filters.ChoiceFilter): A filter field for filtering by specific dates.
        created_between (django_filters.DateFromToRangeFilter): A filter field for filtering
            by a range of dates.

    Methods:
        filter_created(self, queryset, name, value): A method for filtering by specific dates.
            It takes a queryset, a field name, and a value as input and returns a filtered queryset.

    """

    created = django_filters.ChoiceFilter(
        field_name="created_at",
        choices=DateFiltersEnum.choices,
        method="filter_created",
        empty_label=_("---"),
    )
    created_between = django_filters.DateFromToRangeFilter(
        field_name="created_at",
        widget=django_filters.widgets.RangeWidget(
            attrs={"placeholder": "YYYY/MM/DD", "type": "date"}
        ),
        label=_("Created between"),
    )

    def filter_created(
        self, queryset: QuerySet[Any], name: str, value: str
    ) -> QuerySet[Any]:
        """
        Filter a queryset by created date.

        Args:
            queryset (QuerySet[Any]): The queryset to filter.
            name (str): The name of the filter field.
            value (str): The value of the filter field.

        Returns:
            QuerySet[Any]: The filtered queryset.

        """
        if not value:
            return queryset

        if value == "today":
            date = timezone.now()
            return queryset.filter(created_at__date=date)

        elif value == "this_week":
            now = timezone.now()
            start = now - timedelta(days=now.weekday())
            end = start + timedelta(days=6)
            return queryset.filter(created_at__date__range=(start.date(), end.date()))

        elif value == "this_month":
            now = timezone.now()
            return queryset.filter(created_at__month=now.month, created_at__year=now.year)

        return queryset

