from django.urls import include
from django.urls import path

from client.views import ClientCreateView
from client.views import ClientDeleteView
from client.views import ClientDetailsView
from client.views import ClientListView
from client.views import ClientUpdateView
from client.views.bank_registerr import BankRegisterView
from client.views.chart_of_accounts import ChartOfAccountClientView
from client.views.expense_create import ExpenseCreateView
from client.views.journal_entry import JournalEntryView
from client.views.transactions import ClientTransactionListView


app_name = "client"

urlpatterns = [
    path("", ClientListView.as_view(), name="list"),
    path("create", ClientCreateView.as_view(), name="create"),
    path("update/<uuid:pk>", ClientUpdateView.as_view(), name="update"),
    path("delete/<uuid:pk>", ClientDeleteView.as_view(), name="delete"),
    path("<uuid:pk>", ClientDetailsView.as_view(), name="details"),
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
