from __future__ import annotations

import pytest
from django.core.management import call_command

from beach_wood_user.models import BWUser
from bookkeeper.models import BookkeeperProxy
from cfo.models import CFOProxy
from client.models import ClientProxy
from client.views import ClientDetailsView
from core.constants.users import CON_ASSISTANT, CON_BOOKKEEPER, CON_CFO, CON_MANAGER


@pytest.fixture(autouse=True)
def setup_groups(db):
    """Ensure required Django auth groups exist before creating users."""
    call_command("create_groups")


@pytest.mark.django_db
class TestClientDetailsPermissions:
    """Tests for ClientDetailsView authorization test_func."""

    def test_manager_access_granted(self, rf):
        """Manager should always have access to client details."""
        user = BWUser.objects.create_user(
            email="manager@example.com",
            password="Password123!",
            user_type=CON_MANAGER,
        )
        client = ClientProxy.objects.create(name="Test Client Manager")
        request = rf.get(f"/client/{client.pk}")
        request.user = user

        view = ClientDetailsView()
        view.request = request
        view.kwargs = {"pk": client.pk}
        view.object = client

        assert view.test_func() is True

    def test_assistant_access_granted(self, rf):
        """Assistant should always have access to client details."""
        user = BWUser.objects.create_user(
            email="assistant@example.com",
            password="Password123!",
            user_type=CON_ASSISTANT,
        )
        client = ClientProxy.objects.create(name="Test Client Assistant")
        request = rf.get(f"/client/{client.pk}")
        request.user = user

        view = ClientDetailsView()
        view.request = request
        view.kwargs = {"pk": client.pk}
        view.object = client

        assert view.test_func() is True

    def test_cfo_assigned_access_granted(self, rf):
        """CFO assigned to client should have access to client details."""
        user = BWUser.objects.create_user(
            email="cfo@example.com",
            password="Password123!",
            user_type=CON_CFO,
        )
        cfo = CFOProxy.objects.get(user=user)
        client = ClientProxy.objects.create(name="Test Client CFO")
        client.cfos.add(cfo)

        request = rf.get(f"/client/{client.pk}")
        request.user = user

        view = ClientDetailsView()
        view.request = request
        view.kwargs = {"pk": client.pk}
        view.object = client

        assert view.test_func() is True

    def test_cfo_unassigned_access_denied(self, rf):
        """CFO not assigned to client should be denied access."""
        user = BWUser.objects.create_user(
            email="cfo_unassigned@example.com",
            password="Password123!",
            user_type=CON_CFO,
        )
        client = ClientProxy.objects.create(name="Test Client Unassigned CFO")

        request = rf.get(f"/client/{client.pk}")
        request.user = user

        view = ClientDetailsView()
        view.request = request
        view.kwargs = {"pk": client.pk}
        view.object = client

        assert view.test_func() is False

    def test_bookkeeper_assigned_access_granted(self, rf):
        """Bookkeeper assigned to client should have access."""
        user = BWUser.objects.create_user(
            email="bookkeeper@example.com",
            password="Password123!",
            user_type=CON_BOOKKEEPER,
        )
        bookkeeper = BookkeeperProxy.objects.get(user=user)
        client = ClientProxy.objects.create(name="Test Client BK")
        client.bookkeepers.add(bookkeeper)

        request = rf.get(f"/client/{client.pk}")
        request.user = user

        view = ClientDetailsView()
        view.request = request
        view.kwargs = {"pk": client.pk}
        view.object = client

        assert view.test_func() is True

    def test_client_get_absolute_url(self):
        """Client.get_absolute_url should return a valid URL string."""
        from client.models import Client
        client = Client.objects.create(name="URL Test Client")
        url = str(client.get_absolute_url())
        assert url == f"/dashboard/client/{client.pk}"

    def test_client_proxy_get_absolute_url(self):
        """ClientProxy.get_absolute_url should return a valid URL string."""
        client = ClientProxy.objects.create(name="URL Test Client Proxy")
        url = str(client.get_absolute_url())
        assert url == f"/dashboard/client/{client.pk}"


