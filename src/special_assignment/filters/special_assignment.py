import django_filters
from django import forms
from django.utils.translation import gettext as _

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from core.choices.special_assignment import SpecialAssignmentStatusEnum
from core.filters.filter_created_mixin import FilterCreatedMixin
from job.models import JobProxy
from special_assignment.models import SpecialAssignmentProxy

_INPUT_CSS = (
    "py-2 px-3 block w-full border-gray-200 rounded-lg text-xs "
    "focus:border-blue-500 focus:ring-blue-500 dark:bg-neutral-800 "
    "dark:border-neutral-700 dark:text-neutral-200"
)


class SpecialAssignmentFilter(FilterCreatedMixin):
    title = django_filters.CharFilter(
        field_name="title",
        lookup_expr="icontains",
        label=_("Assignment Title"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Search by title..."),
                "class": _INPUT_CSS,
            }
        ),
    )
    status = django_filters.ChoiceFilter(
        field_name="status",
        choices=SpecialAssignmentStatusEnum.choices,
        label=_("Status"),
        empty_label=_("All Statuses"),
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
    assigned_to = django_filters.ModelChoiceFilter(
        field_name="assigned_to",
        queryset=BWUser.objects
        .filter(is_active=True)
        .only("id", "first_name", "last_name", "user_type")
        .order_by("first_name", "last_name"),
        label=_("Assigned To"),
        empty_label=_("All Staff"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    assigned_by = django_filters.ModelChoiceFilter(
        field_name="assigned_by",
        queryset=BWUser.objects
        .filter(is_active=True)
        .only("id", "first_name", "last_name", "user_type")
        .order_by("first_name", "last_name"),
        label=_("Assigned By"),
        empty_label=_("All Staff"),
        widget=forms.Select(attrs={"class": _INPUT_CSS}),
    )
    is_seen = django_filters.BooleanFilter(
        field_name="is_seen",
        label=_("Seen Status"),
        widget=forms.Select(
            choices=[
                ("", _("All")),
                ("true", _("Seen")),
                ("false", _("Unseen")),
            ],
            attrs={"class": _INPUT_CSS},
        ),
    )
    due_date = django_filters.DateFromToRangeFilter(
        field_name="due_date",
        widget=django_filters.widgets.DateRangeWidget(
            attrs={
                "placeholder": "YYYY-MM-DD",
                "type": "date",
                "class": _INPUT_CSS,
            }
        ),
        label=_("Due Date Range"),
    )
    start_date = django_filters.DateFromToRangeFilter(
        field_name="start_date",
        widget=django_filters.widgets.DateRangeWidget(
            attrs={
                "placeholder": "YYYY-MM-DD",
                "type": "date",
                "class": _INPUT_CSS,
            }
        ),
        label=_("Start Date Range"),
    )

    class Meta:
        model = SpecialAssignmentProxy
        fields = [
            "title",
            "status",
            "client",
            "job",
            "assigned_to",
            "assigned_by",
            "is_seen",
            "due_date",
            "start_date",
        ]
