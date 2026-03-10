# -*- coding: utf-8 -*-#
from django.urls import path, include
from dashboard.views.manager import (
    DashboardViewBW,
    ManagerKPIStatsAPIView,
    ManagerPastDueJobsAPIView,
    ManagerTasksThisWeekAPIView,
    ManagerStaffWorkloadAPIView,
    ManagerJobCompletionRateAPIView,
)

app_name = "manager"

urlpatterns = [
    path("", DashboardViewBW.as_view(), name="home"),
    path("api/", include([
        # Existing API
        path("management-dashboard-api/", include("dashboard.urls.api"), name="management-dashboard-api"),
        
        # NEW Phase 1 - Manager Dashboard Widgets
        path(
            "kpi-stats/",
            ManagerKPIStatsAPIView.as_view(),
            name="kpi-stats",
        ),
        path(
            "past-due-jobs/",
            ManagerPastDueJobsAPIView.as_view(),
            name="past-due-jobs",
        ),
        path(
            "tasks-this-week/",
            ManagerTasksThisWeekAPIView.as_view(),
            name="tasks-this-week",
        ),
        path(
            "staff-workload/",
            ManagerStaffWorkloadAPIView.as_view(),
            name="staff-workload",
        ),
        path(
            "job-completion-rate/",
            ManagerJobCompletionRateAPIView.as_view(),
            name="job-completion-rate",
        ),
    ])),
]
