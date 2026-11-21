# -*- coding: utf-8 -*-#
from .dashboard import DashboardViewBW
from .api import (
    ManagementDashboardApiView,
    ManagerKPIStatsAPIView,
    ManagerPastDueJobsAPIView,
    ManagerTasksThisWeekAPIView,
    ManagerStaffWorkloadAPIView,
    ManagerJobCompletionRateAPIView,
)

__all__ = [
    "DashboardViewBW",
    "ManagementDashboardApiView",
    "ManagerKPIStatsAPIView",
    "ManagerPastDueJobsAPIView",
    "ManagerTasksThisWeekAPIView",
    "ManagerStaffWorkloadAPIView",
    "ManagerJobCompletionRateAPIView",
]
