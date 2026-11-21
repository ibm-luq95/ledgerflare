from typing import Optional

import click
from django.core.paginator import Page, Paginator
from django.db import transaction
from django.db.models import Q

from client.models.helpers.map_helper import ClientDetailsMap
from client.models.querysets.types import ClientJobsFilterTypes
from core.models.querysets import BaseQuerySetMixin
from core.utils import bw_log


class ClientReportsQuerySet(BaseQuerySetMixin):
    def get_all_jobs_as_list(
        self,
        filter_params: ClientJobsFilterTypes | None = None,
        page: int | None = None,
        per_page: int | None = 15,
    ) -> dict[int, Page, list[ClientDetailsMap]]:
        # DebuggingPrint.pprint(locals())
        from client.models.client_proxy import ClientProxy

        # DebuggingPrint.pprint(filter_params)
        with transaction.atomic():
            data_list: list[dict] = list()
            years_list = set()
            created_year = filter_params.get("created_year")
            clients_pks = filter_params.get("clients")
            client_categories = filter_params.get("categories")
            job_categories = filter_params.get("job_categories")
            job_status = filter_params.get("job_status")
            job_type = filter_params.get("job_type")
            job_stats = filter_params.get("job_stats")
            jobs_managed_by = filter_params.get("managed_by")
            period_year = filter_params.get("period_year")
            period_month = filter_params.get("period_month")
            # debugging_print(filter_params)
            clients_q = Q()
            if client_categories is not None:
                clients_q &= Q(categories__in=client_categories)
            if clients_pks is not None:
                clients_q &= Q(pk__in=clients_pks)
            if job_categories is not None:
                clients_q &= Q(jobs__categories__in=job_categories)
            if job_stats is not None:
                clients_q &= Q(jobs__stats__in=job_stats)
            if job_type is not None:
                clients_q &= Q(jobs__type__in=job_type)
            if job_status is not None:
                clients_q &= Q(jobs__status__in=job_status)
            if jobs_managed_by is not None:
                clients_q &= Q(jobs__managed_by__in=jobs_managed_by)
            if period_year is not None:
                clients_q &= Q(jobs__period_year__in=[int(period_year)])
            try:
                details_dict = dict()
                clients = (
                    ClientProxy.objects.select_related()
                    # .annotate(period_year=Cast("jobs__period_year", CharField()))
                    .filter(clients_q)
                    .distinct()
                    .order_by("name")
                )
                details_dict.setdefault("total_rows_count", len(clients))
                page_object = Paginator(clients, per_page)
                details_dict.setdefault("page_obj", page_object.get_page(page))
                for client in page_object.page(page).object_list:
                    q_objects = Q(client_id=client.pk)
                    if (
                        period_year is not None and period_year.isdigit() is True
                    ):  # it should be letter case
                        q_objects &= Q(job_period_year=str(period_year))
                    if (
                        period_month is not None and period_month.isdigit() is True
                    ):  # it should be letter case
                        q_objects &= Q(job_period_month=str(period_month))
                    client_details_map = ClientDetailsMap(
                        client=client, filtered_by_year=period_year
                    )
                    tmp_data = {
                        "map_obj": client_details_map,
                        "client_obj": client,
                        "serialized_obj": client_details_map.serializer(),
                    }
                    data_list.append(tmp_data)
                # DebuggingPrint.pprint(data_list)
                details_dict.setdefault("object_list", data_list)
                details_dict.setdefault("current_object_list_count", len(data_list))
                # DebuggingPrint.pprint(details_dict)
                return details_dict
            except Exception:
                bw_log().print_exception(suppress=[click], show_locals=False)
                # colored_output_with_logging(
                #     is_logged=True,
                #     text=traceback.format_exc(),
                #     log_level="error",
                #     color="red",
                # )
