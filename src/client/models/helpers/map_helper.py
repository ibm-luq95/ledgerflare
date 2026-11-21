from collections import defaultdict
from typing import Optional

from django.db.models import Q

from core.utils import get_months_abbr
from reports.models import ClientJobsReportsDBView


class ClientDetailsMap:
    JOBS_FIELD_NAMES = [
        "job_completed_count",
        "job_not_completed_count",
        "job_past_due_count",
        "job_in_progress_count",
        "job_archived_count",
        "job_not_started_count",
        "job_draft_count",
    ]

    def __init__(self, client, filtered_by_year: str | int | None = None):
        """
        Initialize the instance with the given client.
        """
        self.client = client
        report_qs_q_obj = Q()
        report_qs_q_obj &= Q(client_id=self.client.pk)
        if filtered_by_year is not None:
            self.filtered_by_year = str(filtered_by_year)
            report_qs_q_obj &= Q(job_period_year=self.filtered_by_year)
        self.reports_qs = ClientJobsReportsDBView.objects.filter(report_qs_q_obj)
        self.reports_qs_count = self.reports_qs.count()
        self.pk = self.client.pk
        self.__years = set()
        self.__total_jobs = 0
        self.__jobs_month = dict()
        self.init_report_years()
        self.init_total_jobs()

    def init_report_years(self):
        """
        Initialize the report years by iterating through the reports query set and adding the job period years to the
        set of years.
        """
        for r in self.reports_qs:
            self.years.add(r.job_period_year)

    def init_total_jobs(self):
        """
        Initialize the total jobs by iterating through the JOBS_FIELD_NAMES attribute
        and reports_qs. Set the total_jobs attribute with the value obtained from the
        reports_qs using the job_field_name as the attribute name.
        """
        for job_field_name in self.JOBS_FIELD_NAMES:
            for r in self.reports_qs:
                self.total_jobs = getattr(r, job_field_name)

    @property
    def years(self):
        """
        Getter method for the years' property.
        """
        return self.__years

    @years.setter
    def years(self, value):
        """
        Setter function for the years attribute.

        Parameters:
        value : the value to set for the years attribute

        Return:
        None
        """
        self.__years.add(value)

    @property
    def total_jobs(self) -> int:
        """
        Return the total number of jobs as an integer.
        """
        return int(self.__total_jobs)

    @total_jobs.setter
    def total_jobs(self, value):
        """
        Setter for total_jobs attribute.

        :param value: The value to add to the total_jobs attribute.
        :return: None
        """
        self.__total_jobs += value

    def serializer(self) -> dict:
        """
        Serialize the object attributes into a dictionary.
        """
        return dict(
            sorted(
                {
                    "client_pk": self.pk,
                    "name": self.client.name,
                    "years": self.years,
                    "total_jobs": self.total_jobs,
                    "reports_qs_count": self.reports_qs_count,
                    "reports_qs": self.reports_qs,
                    "organize_by_year": self.organize_by_year(),
                    "organize_by_month": self.organize_by_month(),
                    "all_reports": self.all_reports(),
                    "has_reports": self.has_reports(),
                }.items()
            )
        )

    def has_reports(self) -> bool:
        """
        Check if the client has any reports.

        :return: True if the client has any reports, False otherwise
        :rtype: bool
        """
        return self.reports_qs_count > 0

    def merge_data_for_all_report(self, dict1: dict, dict2: dict) -> dict:
        """
        Merges data from dict2 into dict1 for all report, and returns the merged dictionary.

        :param dict1: The first dictionary to be merged
        :type dict1: dict
        :param dict2: The second dictionary to be merged
        :type dict2: dict
        :return: The merged dictionary
        :rtype: dict
        """
        # {
        #     "client_id": self.client_id,
        #     "client_name": self.client_name,
        #     "job_completed_count": int(self.job_completed_count),
        #     "job_not_completed_count": int(self.job_not_completed_count),
        #     "job_past_due_count": int(self.job_past_due_count),
        #     "job_in_progress_count": int(self.job_in_progress_count),
        #     "job_archived_count": int(self.job_archived_count),
        #     "job_not_started_count": int(self.job_not_started_count),
        #     "job_draft_count": int(self.job_draft_count),
        #     "job_period_month": int(self.job_period_month),
        #     "job_period_year": int(self.job_period_year),
        # }
        dict1["job_completed_count"] += dict2["job_completed_count"]
        dict1["job_not_completed_count"] += dict2["job_not_completed_count"]
        dict1["job_past_due_count"] += dict2["job_past_due_count"]
        dict1["job_in_progress_count"] += dict2["job_in_progress_count"]
        dict1["job_archived_count"] += dict2["job_archived_count"]
        dict1["job_not_started_count"] += dict2["job_not_started_count"]
        dict1["job_draft_count"] += dict2["job_draft_count"]
        dict1["job_period_month"] = dict2["job_period_month"]
        dict1["job_period_year"] = dict2["job_period_year"]

        return dict1

    def all_reports(
        self,
    ) -> dict[str, dict[str, None]] | dict[str, dict[str, None] | str | None] | None:
        """
        This function retrieves all reports and organizes them by month, updating the months_data dictionary with the
        relevant counts. It returns the updated months_data dictionary if successful, or None if orgs_months is None.
        """
        # DebuggingPrint.pprint(self.reports_qs_count)
        orgs_months = self.organize_by_month()
        # DebuggingPrint.pprint(orgs_months)
        if orgs_months is None:
            return None
        all_data = self.create_all_months_template(is_with_year=False)
        all_data.update({"is_all_report": True})
        for item in orgs_months:
            item_data = item.get("data")
            for m_idx, m_data in item_data.items():
                if m_data:
                    if all_data["data"][m_idx] is not None:
                        ff = self.merge_data_for_all_report(
                            all_data["data"][m_idx], m_data
                        )
                        # DebuggingPrint.pprint(ff)
                        all_data["data"][m_idx] = ff
                    else:
                        all_data["data"][m_idx] = m_data
        # DebuggingPrint.pprint(all_data)
        return all_data

    def create_all_months_template(
        self, year: int | str | None = None, is_with_year: bool = True
    ) -> dict[str, dict[str, None]] | dict[str, dict[str, None] | str | None]:
        """
        Create a template for all months in a given year.

        Parameters:
            year (Optional[int | str]): The year for which the template is created.
                                       Defaults to None.
            is_with_year (bool): Indicates whether the year should be included in the
                                 template. Defaults to True.

        Returns:
            dict[str, dict[str, None]] | dict[str, dict[str, None] | str | None]: The
            template for all months in the given year.
        """
        if year is not None:
            if isinstance(year, int) is True:
                year = str(year)
        months_idx = get_months_abbr(return_months_idxs=True)
        months_idx = set([str(m) for m in months_idx])
        months_idx = list(months_idx)
        months_idx.sort(key=int)
        data = dict.fromkeys(months_idx)
        if is_with_year is False:
            return {"data": data}
        return {"year": year, "data": data}

    def organize_by_year(self) -> dict[str, ClientJobsReportsDBView] | None:
        """
        Organizes the reports by year.

        Returns:
        - A dictionary where the keys are years and the values are ClientJobsReportsDBView objects,
          or None if self.years is empty.
        """
        if not self.years:
            return None
        # Create a dictionary where the keys are years and the values are the filtered reports for each year
        data = {year: self.reports_qs.filter(job_period_year=year) for year in self.years}
        # DebuggingPrint.pprint(data)
        return data

    def organize_by_month(self) -> list[dict] | None:
        """
        Organizes data by month based on the data organized by year.
        Returns a dictionary with years as keys and a list of instances as values.
        """
        years_orgs = self.organize_by_year()
        # DebuggingPrint.pprint(years_orgs)
        if years_orgs is None:
            return None
        years_dict = defaultdict(list)
        full_months_data: list[dict] = []
        for year, jobs_qs in years_orgs.items():
            months_years_dict = self.create_all_months_template(year)
            # DebuggingPrint.pprint(months_years_dict["data"])
            if jobs_qs:
                for qs in jobs_qs:
                    years_dict[year].append(qs.get_instance_as_dict)
                    # months_years_dict["data"][
                    # 	str(qs.get_instance_as_dict.get("job_period_month"))
                    # ].append(qs.get_instance_as_dict)
                    months_years_dict["data"][
                        str(qs.get_instance_as_dict.get("job_period_month"))
                    ] = qs.get_instance_as_dict
            # else:
            # 	months_years_dict["data"][
            # 		str(qs.get_instance_as_dict.get("job_period_month"))
            # 	] = []

            full_months_data.append(months_years_dict)
        # DebuggingPrint.pprint(years_dict)
        # DebuggingPrint.pprint(full_months_data)
        return full_months_data

    def __repr__(self):
        return (
            f"Client: PK: {self.pk}, Name: {self.client.name}, Years: {self.years}, Total QS Count: "
            f"{self.reports_qs_count}"
        )
