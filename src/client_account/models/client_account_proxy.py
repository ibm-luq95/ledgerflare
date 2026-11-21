# -*- coding: utf-8 -*-#
from __future__ import annotations

from client_account.models.client_account import ClientAccount


class ClientAccountProxy(ClientAccount):
    """Proxy model for ClientAccount for guardian object-level permissions and FK referencing."""

    class Meta(ClientAccount.Meta):
        proxy = True
        indexes = []
