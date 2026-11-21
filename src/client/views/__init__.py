"""Client views package providing CRUD, API, export, and quick-peek views."""

from __future__ import annotations

from .api import ClientViewSet
from .client import (
    BaseClientExportView,
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


__all__ = [
    "BaseClientExportView",
    "ClientCreateView",
    "ClientDeleteView",
    "ClientDetailsView",
    "ClientExportCsvView",
    "ClientExportExcelView",
    "ClientExportView",
    "ClientListView",
    "ClientQuickPeekView",
    "ClientUpdateView",
    "ClientViewSet",
]
