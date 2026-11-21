from __future__ import annotations

from django.urls import include, path

from client.views import (
    ClientCreateView,
    ClientDeleteView,
    ClientDetailsView,
    ClientExportCsvView,
    ClientExportExcelView,
    ClientExportView,
    ClientListView,
    ClientQuickPeekView,
    ClientUpdateView,
)
from client.views.bank_registerr import BankRegisterView
from client.views.chart_of_accounts import ChartOfAccountClientView
from client.views.expense_create import ExpenseCreateView
from client.views.journal_entry import JournalEntryView
from client.views.transactions import ClientTransactionListView


app_name = "client"

urlpatterns = [
    path("", ClientListView.as_view(), name="list"),
    path("export/", ClientExportView.as_view(), name="export"),
    path("export/csv/", ClientExportCsvView.as_view(), name="export_csv"),
    path("export/excel/", ClientExportExcelView.as_view(), name="export_excel"),
    path("create", ClientCreateView.as_view(), name="create"),
    path("update/<uuid:pk>", ClientUpdateView.as_view(), name="update"),
    path("delete/<uuid:pk>", ClientDeleteView.as_view(), name="delete"),
    path("<uuid:pk>", ClientDetailsView.as_view(), name="details"),
    path("<uuid:pk>/quick-peek/", ClientQuickPeekView.as_view(), name="quick-peek"),
    path("api/", include("client.urls.api"), name="api"),
    path("transactions/", ClientTransactionListView.as_view(), name="transactions"),
    path("journal-entry/", JournalEntryView.as_view(), name="journal_entry"),
    path("bank-register/", BankRegisterView.as_view(), name="bank_register"),
    path(
        "chart-of-accounts/",
        ChartOfAccountClientView.as_view(),
        name="chart_of_accounts",
    ),
    path(
        "expense-create/",
        ExpenseCreateView.as_view(),
        name="expense_create",
    ),
]
