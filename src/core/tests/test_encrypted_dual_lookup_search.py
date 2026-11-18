"""Unit tests for dual-lookup search on encrypted models with trigram blind indexes."""

from __future__ import annotations

import pytest
from django.db.models import Q

from client_account.filters import ClientAccountFilter
from client_account.models import ClientAccountProxy


@pytest.mark.django_db
def test_client_account_search_matches_both_plaintext_and_trigram_index() -> None:
    """Verify ClientAccount search matches both legacy plaintext and encrypted trigram index."""
    # 1. Plaintext unmigrated account
    acc1 = ClientAccountProxy.objects.create(
        account_name="Unmigrated Chase",
        account_url="https://chase.com/login",
        account_username="plain_user",
    )
    # Manually simulate unmigrated row by clearing bidx arrays and raw value
    ClientAccountProxy.objects.filter(pk=acc1.pk).update(
        account_url_bidx=[],
        account_username_bidx=[],
    )

    # 2. Migrated account with trigrams
    acc2 = ClientAccountProxy.objects.create(
        account_name="Migrated Chase",
        account_url="https://chase.com/portal",
        account_username="migrated_secure_user",
    )
    acc2.refresh_from_db()
    assert len(acc2.account_url_bidx) > 0

    # Search via ClientAccountFilter
    filter_set = ClientAccountFilter(
        data={"account_url": "chase"},
        queryset=ClientAccountProxy.objects.all(),
    )
    results = list(filter_set.qs)
    assert acc1 in results
    assert acc2 in results


@pytest.mark.django_db
def test_staff_accounts_viewset_search_trigram_support() -> None:
    """Verify StaffAccountsViewSet search query matches username_email via trigram blind index."""
    from django.core.management import call_command
    from django.urls import reverse
    from rest_framework.test import APIClient

    from beach_wood_user.models import BWUser
    from core.choices import BeachWoodUserTypeEnum
    from staff_briefcase.models import StaffAccounts, StaffBriefcase

    call_command("create_groups")

    manager = BWUser.objects.create_user(
        email="mgr_search_test@example.com",
        password="ValidPassword123!",
        user_type=BeachWoodUserTypeEnum.MANAGER,
    )
    briefcase, _ = StaffBriefcase.objects.get_or_create(user=manager)

    acc = StaffAccounts.objects.create(
        title="QuickBooks Staff",
        username_email="bookkeeper@beachwood.com",
    )
    briefcase.accounts.add(acc)
    acc.refresh_from_db()
    assert len(acc.username_email_bidx) > 0

    url = reverse(
        "dashboard:briefcase:briefcase_staff_accounts:api:staff-accounts-api-router-list"
    )
    client = APIClient()
    client.force_authenticate(user=manager)
    response = client.get(f"{url}?search=beachwood")
    assert response.status_code == 200

    results = response.data.get("results", response.data)
    ids = [item["id"] for item in results]
    assert str(acc.pk) in ids
