"""Jobs report filter form."""
from __future__ import annotations

from typing import ClassVar

from django import forms
from django.http import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from client_category.models import ClientCategory
from core.choices.fiscal_year import FiscalYearEnum
from core.forms.mixins.base_form_mixin import BWBaseFormMixin
from job_category.models import JobCategory
from reports.forms.mixins.set_initial_form_inputs_mixin import (
    SetInitialFilterFormInputsMixin,
)
from reports.forms.mixins.shared_filters_inputs_mixin import (
    SharedFilterInputsMixin,
)


class ClientJobsFilter(
    BWBaseFormMixin, SharedFilterInputsMixin, SetInitialFilterFormInputsMixin
):
    """Filter form for client jobs report."""

    ORDER_CHOICES: ClassVar[list[tuple[str, str]]] = [
        ("current_week", _("Current Week Jobs (Due this week)")),
        ("most_jobs_count", _("Most Jobs Count")),
        ("most_jobs", _("Most Jobs (Annual / Period)")),
        ("least_jobs", _("Least Jobs Count")),
        ("name_asc", _("Client Name (A to Z)")),
        ("name_desc", _("Client Name (Z to A)")),
    ]

    HEALTH_CHOICES: ClassVar[list[tuple[str, str]]] = [
        ("all", _("All Health Statuses")),
        ("action_needed", _("🔴 Action Needed (Past Due ≥ 3)")),
        ("at_risk", _("🟡 At Risk (Past Due 1-2)")),
        ("on_track", _("🟢 On Track (No Delays)")),
    ]

    field_order: ClassVar[list[str]] = [
        "clients",
        "categories",
        "job_categories",
        "period_year",
        "managed_by",
        "health_status",
        "order_by",
    ]

    clients = forms.ModelMultipleChoiceField(
        label=_("Client"),
        queryset=ClientProxy.objects.order_by("name"),
        required=False,
        help_text=_("Filter by specific clients"),
    )
    categories = forms.ModelMultipleChoiceField(
        label=_("Client category"),
        queryset=ClientCategory.objects.order_by("name"),
        required=False,
        help_text=_("Filter by client categories"),
    )
    job_categories = forms.ModelMultipleChoiceField(
        label=_("Job category"),
        queryset=JobCategory.objects.order_by("name"),
        required=False,
        help_text=_("Filter by job category"),
    )
    period_year = forms.ChoiceField(
        label=_("Period year"),
        required=False,
        choices=FiscalYearEnum.choices,
        help_text=_("Filter by fiscal year"),
    )
    managed_by = forms.ModelMultipleChoiceField(
        queryset=BWUser.objects.all(),
        label=_("Managed by"),
        required=False,
        help_text=_("Filter by managing staff member"),
    )
    health_status = forms.ChoiceField(
        label=_("Health Status"),
        required=False,
        choices=HEALTH_CHOICES,
        help_text=_("Filter clients by delivery risk status"),
    )
    order_by = forms.ChoiceField(
        label=_("Sort By"),
        required=False,
        choices=ORDER_CHOICES,
        help_text=_("Order clients by weekly workload, total jobs, or name"),
    )

    def __init__(
        self,
        request: HttpRequest | None = None,
        *args,
        **kwargs,
    ) -> None:
        """Initialize filter form with request parameters and defaults."""
        super().__init__(*args, **kwargs)
        SetInitialFilterFormInputsMixin.__init__(self, request=request)
        self.fields.pop("quick_created_at", None)
        self.fields.pop("created_at", None)
        self.fields.pop("created_year", None)

        if not self.fields["period_year"].initial:
            self.fields["period_year"].initial = str(timezone.now().year)
        if not self.fields["order_by"].initial:
            self.fields["order_by"].initial = "current_week"
        if not self.fields["health_status"].initial:
            self.fields["health_status"].initial = "all"

    def serialize_inputs(self) -> dict:
        """Serialize current form inputs to dictionary."""
        data = {}
        if self.is_bound and self.is_valid():
            for name, value in self.cleaned_data.items():
                data[name] = value or self.fields[name].initial
        else:
            for name, field in self.fields.items():
                data[name] = field.initial
        return data
