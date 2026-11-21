from dataclasses import dataclass
from datetime import date
from typing import NotRequired, Optional, TypedDict
from uuid import UUID

from django.utils.translation import gettext as _


class ClientJobsFilterTypes(TypedDict):
    clients: NotRequired[list]
    categories: NotRequired[list]
    job_categories: NotRequired[list]
    managed_by: NotRequired[list]
    created_at: NotRequired[date]
    months: NotRequired[list]
    job_stats: NotRequired[list]
    created_year: NotRequired[str]
    job_status: NotRequired[list]
    job_type: NotRequired[list]
    quick_created_at: NotRequired[str]
    period_month: NotRequired[str]
    period_year: NotRequired[str]


# @dataclass(order=True, init=False)
class JobItemDictType(TypedDict):
    client_name: str | None
    id: UUID
    job_month: int
    job_year: str | None
    job_completed_count: int
    job_draft_count: int
    job_in_progress_count: int
    job_not_completed_count: int
    job_not_started_count: int
    job_past_due_count: int
    job_archived_count: int


TYPED_ALL_ITEM = {
    "client_name": "",
    "id": "",
    "job_archived_count": 0,
    "job_completed_count": 0,
    "job_draft_count": 0,
    "job_in_progress_count": 0,
    "job_month": 0,
    "job_not_completed_count": 0,
    "job_not_started_count": 0,
    "job_past_due_count": 0,
    "job_year": _("All"),
}
