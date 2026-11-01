"""Tests for on-demand password reveal API endpoints."""

from __future__ import annotations

import pytest
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from client_account.models import ClientAccountProxy
from core.choices import BeachWoodUserTypeEnum
from staff_briefcase.models import StaffAccounts, StaffBriefcase


@pytest.fixture(autouse=True)
def setup_groups(db: None) -> None:
    """Ensure Django auth groups exist before running reveal tests."""
    call_command("create_groups")


@pytest.mark.django_db
class TestPasswordRevealApi:
    """Verify on-demand reveal endpoint security, permissions, and auditing."""

    def test_anonymous_cannot_reveal_password(self) -> None:
        """Unauthenticated request must return 401 Unauthorized."""
        client_obj = ClientProxy.objects.create(name="Vault Client")
        account = ClientAccountProxy.objects.create(
            client=client_obj,
            account_name="Bank Portal",
            account_password="SuperSecretPassword123!",
        )

        client = APIClient()
        url = reverse(
            "dashboard:client_account:api:reveal-password", kwargs={"pk": account.pk}
        )
        response = client.post(url)
        assert response.status_code in (401, 403)

    def test_unassigned_bookkeeper_denied_reveal(self) -> None:
        """Bookkeeper not assigned to client must receive 403 Forbidden."""
        bk_assigned = BWUser.objects.create_user(
            email="assigned_rev@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.BOOKKEEPER,
        )
        bk_unassigned = BWUser.objects.create_user(
            email="unassigned_rev@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.BOOKKEEPER,
        )

        client_obj = ClientProxy.objects.create(name="Vault Client 2")
        client_obj.bookkeepers.add(bk_assigned.bookkeeper.get_proxy_model())

        account = ClientAccountProxy.objects.create(
            client=client_obj,
            account_name="IRS Portal",
            account_password="SuperSecretPassword123!",
        )

        client = APIClient()
        client.force_authenticate(user=bk_unassigned)
        url = reverse(
            "dashboard:client_account:api:reveal-password", kwargs={"pk": account.pk}
        )
        response = client.post(url)
        assert response.status_code == 403

    def test_assigned_bookkeeper_can_reveal_password(self) -> None:
        """Assigned bookkeeper receives decrypted password on demand."""
        bk_assigned = BWUser.objects.create_user(
            email="assigned_rev2@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.BOOKKEEPER,
        )

        client_obj = ClientProxy.objects.create(name="Vault Client 3")
        client_obj.bookkeepers.add(bk_assigned.bookkeeper.get_proxy_model())

        account = ClientAccountProxy.objects.create(
            client=client_obj,
            account_name="Payroll Portal",
            account_password="DecryptedPayrollPass!",
        )

        client = APIClient()
        client.force_authenticate(user=bk_assigned)
        url = reverse(
            "dashboard:client_account:api:reveal-password", kwargs={"pk": account.pk}
        )
        response = client.post(url)
        assert response.status_code == 200
        assert response.data.get("password") == "DecryptedPayrollPass!"
        assert response.data.get("status") == "success"

    def test_other_user_cannot_reveal_staff_account_password(self) -> None:
        """User cannot reveal credentials of another staff member's briefcase account."""
        owner = BWUser.objects.create_user(
            email="owner_acc@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.BOOKKEEPER,
        )
        intruder = BWUser.objects.create_user(
            email="intruder_acc@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.BOOKKEEPER,
        )

        briefcase_owner, _ = StaffBriefcase.objects.get_or_create(user=owner)
        account = StaffAccounts.objects.create(
            name="Private Account",
            title="Private Access",
            username_email="private@vault.com",
            password="OwnerVaultPass123!",
        )
        briefcase_owner.accounts.add(account)

        client = APIClient()
        client.force_authenticate(user=intruder)
        url = reverse(
            "dashboard:briefcase:briefcase_staff_accounts:api:reveal-password",
            kwargs={"pk": account.pk},
        )
        response = client.post(url)
        assert response.status_code == 403

    def test_owner_can_reveal_staff_account_password(self) -> None:
        """Owner receives decrypted password for their own briefcase account."""
        owner = BWUser.objects.create_user(
            email="owner_acc2@example.com",
            password="ValidPassword123!",
            user_type=BeachWoodUserTypeEnum.BOOKKEEPER,
        )

        briefcase_owner, _ = StaffBriefcase.objects.get_or_create(user=owner)
        account = StaffAccounts.objects.create(
            name="Private Account 2",
            title="Private Access 2",
            username_email="private2@vault.com",
            password="OwnerVaultPass123!",
        )
        briefcase_owner.accounts.add(account)

        client = APIClient()
        client.force_authenticate(user=owner)
        url = reverse(
            "dashboard:briefcase:briefcase_staff_accounts:api:reveal-password",
            kwargs={"pk": account.pk},
        )
        response = client.post(url)
        assert response.status_code == 200
        assert response.data.get("password") == "OwnerVaultPass123!"
        assert response.data.get("status") == "success"
