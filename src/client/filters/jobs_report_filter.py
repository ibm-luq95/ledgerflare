import django_filters
from django import forms
from django.utils.translation import gettext as _

from core.filters.filter_created_mixin import FilterCreatedMixin
from job.models import JobProxy
from job_category.models import JobCategory


class JobReportFilter(FilterCreatedMixin):
    categories = django_filters.ModelMultipleChoiceFilter(
        field_name="categories",
        queryset=JobCategory.objects.all(),
        # widget=forms.CheckboxSelectMultiple,
        lookup_expr="exact",
        help_text=_("Jobs categories"),
    )
    due_date__gt = django_filters.DateFilter(
        field_name="due_date",
        widget=forms.DateInput(attrs={"type": "date"}),
        lookup_expr="gt",
        label=_("Due date greater than"),
    )
    due_date__lt = django_filters.DateFilter(
        field_name="due_date",
        widget=forms.DateInput(attrs={"type": "date"}),
        lookup_expr="lt",
        label=_("Due date less than"),
    )
    created_at = django_filters.DateFilter(
        field_name="created_at", widget=forms.DateInput(attrs={"type": "date"})
    )

    class Meta:
        model = JobProxy
        fields = {
            "title": ["icontains"],
            "client": ["exact"],
            "managed_by": ["exact"],
            "status": ["exact"],
            "job_type": ["exact"],
            "state": ["exact"],
            "description": ["icontains"],
        }
        # fields = {
        #     "name": ["icontains"],
        #     "bookkeepers": ["exact"],
        #     "email": ["exact"],
        #     "city": ["exact"],
        #     "state": ["exact"],
        #     "street": ["icontains"],
        #     "status": ["exact"],
        # }
