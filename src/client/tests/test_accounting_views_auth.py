"""Tests verifying authentication on accounting views and CFO archive scoping."""

from __future__ import annotations

import pytest
from django.core.management import call_command
from django.test import Client, RequestFactory
from django.urls import reverse

from archive.views.job import JobArchiveListView
from beach_wood_user.models import BWUser
from client.models import ClientProxy
from client.views.bank_registerr import BankRegisterView
from client.views.chart_of_accounts import ChartOfAccountClientView
from client.views.expense_create import ExpenseCreateView
from client.views.journal_entry import JournalEntryView
from client.views.transactions import ClientTransactionListView
from core.choices import BeachWoodUserTypeEnum
from core.constants.users import CON_CFO
from core.views.mixins import BWLoginRequiredMixin
from job.models import JobProxy


@pytest.fixture(autouse=True)
def setup_groups(db: None) -> None:
    """Ensure Django auth groups exist before running accounting tests."""
    call_command("create_groups")


@pytest.mark.django_db
class TestAccountingViewsAuth:
    """Verify that accounting views require authentication and archive lists scope for CFO."""

    def test_accounting_views_inherit_login_required(self) -> None:
        """All 5 accounting template views must inherit BWLoginRequiredMixin."""
        assert issubclass(ClientTransactionListView, BWLoginRequiredMixin)
        assert issubclass(ExpenseCreateView, BWLoginRequiredMixin)
        assert issubclass(JournalEntryView, BWLoginRequiredMixin)
        assert issubclass(BankRegisterView, BWLoginRequiredMixin)
        assert issubclass(ChartOfAccountClientView, BWLoginRequiredMixin)

    def test_anonymous_redirected_from_accounting_views(self) -> None:
        """Unauthenticated requests to accounting views must redirect to login (302)."""
        client = Client()
        urls = [
            reverse("dashboard:client:transactions"),
            reverse("dashboard:client:journal_entry"),
            reverse("dashboard:client:bank_register"),
            reverse("dashboard:client:chart_of_accounts"),
            reverse("dashboard:client:expense_create"),
        ]
        for url in urls:
            response = client.get(url)
            assert response.status_code == 302
            assert "/auth/login" in response.url

    def test_cfo_archive_job_scoping(self, rf: RequestFactory) -> None:
        """CFO user only sees archived jobs for assigned clients."""
        cfo_user = BWUser.objects.create_user(
            email="cfo_archive@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.CFO,
        )

        client_assigned = ClientProxy.objects.create(name="CFO Client Assigned")
        client_assigned.cfos.add(cfo_user.cfo.get_proxy_model())

        client_unassigned = ClientProxy.objects.create(name="CFO Client Unassigned")

        # Create archived jobs
        job_assigned = JobProxy.objects.create(
            title="Archived Assigned Job",
            client=client_assigned,
            status="archived",
            is_deleted=False,
        )
        job_unassigned = JobProxy.objects.create(
            title="Archived Unassigned Job",
            client=client_unassigned,
            status="archived",
            is_deleted=False,
        )

        view = JobArchiveListView()
        req = rf.get("/dashboard/archive/jobs/archive")
        req.user = cfo_user
        view.request = req
        qs = view.get_queryset()

        assert qs.filter(pk=job_assigned.pk).exists()
        assert not qs.filter(pk=job_unassigned.pk).exists()
