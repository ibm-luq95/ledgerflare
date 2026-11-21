from typing import Optional

from django.core.paginator import Page
from django.db.models import Q

from client.models.helpers.map_helper import ClientDetailsMap
from client.models.querysets.reports_qs import ClientReportsQuerySet
from client.models.querysets.types import ClientJobsFilterTypes
from core.models.managers import SoftDeleteManager
from core.models.querysets import BaseQuerySetMixin


class ClientReportsManager(SoftDeleteManager):
    def get_queryset(self) -> ClientReportsQuerySet:
        queryset = ClientReportsQuerySet(self.model, using=self._db).filter(
            Q(is_deleted=False)
        )
        return queryset

    def all(self) -> BaseQuerySetMixin:
        return self.get_queryset().order_by("name")

    def get_all_jobs_as_list(
        self,
        filter_params: ClientJobsFilterTypes | None = None,
        page: int | None = None,
        per_page: int | None = 15,
    ) -> dict[int, Page, list[ClientDetailsMap]]:
        qs = self.get_queryset()

        return qs.get_all_jobs_as_list(filter_params, page, per_page)
