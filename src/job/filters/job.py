# -*- coding: utf-8 -*-#
import django_filters
from django import forms
from django.db.models.sql.where import WhereNode

from core.filters.filter_created_mixin import FilterCreatedMixin
from core.filters.filter_help_text import HelpfulFilterSet
from core.utils.developments.debugging_print_object import DebuggingPrint
from job.models import JobProxy
from job_category.models import JobCategory
from django.utils.translation import gettext as _


class JobFilter(FilterCreatedMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # DebuggingPrint.pprint(self.form.fields.items())
        self.form.fields.pop("created_between")

    due_date = django_filters.DateFilter(
        field_name="due_date", widget=forms.DateInput(attrs={"type": "date"})
    )
    due_date__gt = django_filters.DateFilter(
        field_name="due_date",
        widget=forms.DateInput(attrs={"type": "date"}),
        lookup_expr="gt",
    )
    due_date__lt = django_filters.DateFilter(
        field_name="due_date",
        widget=forms.DateInput(attrs={"type": "date"}),
        lookup_expr="lt",
    )
    categories = django_filters.ModelMultipleChoiceFilter(
        field_name="categories",
        queryset=JobCategory.objects.all(),
        # widget=forms.CheckboxSelectMultiple,
        widget=forms.SelectMultiple(attrs={"data_name": "job-categories"}),
        lookup_expr="exact",
    )
    # show_all = django_filters.ChoiceFilter(
    #     label=_("Show all jobs"),
    #     method="filter_show_all",
    #     help_text=_("Check this box to show all jobs."),
    #     choices=[
    #         ("true", _("Yes")),
    #     ],
    #     empty_label=_("Select an option"),
    # )

    # def filter_show_all(self, queryset, name, value):
    #     if value:
    #         # Capture existing filters
    #         where_clause: WhereNode = queryset.query.where
    #         DebuggingPrint.print(where_clause)
    #         # DebuggingPrint.inspect(where_clause, is_all=True)
    #         # DebuggingPrint.print(type(where_clause))
    #         DebuggingPrint.pprint(where_clause.get_source_expressions())
    #
    #         # Create new queryset with original manager
    #         new_qs = JobProxy.original_objects.all()
    #
    #         # Apply captured filters to new manager
    #         return new_qs.filter(where_clause)
    #
    #     return queryset

    class Meta:
        model = JobProxy
        fields = {
            "title": ["icontains"],
            "managed_by": ["exact"],
            "period_year": ["exact"],
            "period_month": ["exact"],
            "client": ["exact"],
            "status": ["exact"],
            "state": ["exact"],
        }
