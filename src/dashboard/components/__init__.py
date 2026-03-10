# -*- coding: utf-8 -*-#
"""
LedgerFlare Dashboard Components

This module contains reusable Django components for the LedgerFlare dashboard.
All components are auto-discovered by django-components.
"""

from .kpi_card import KPICard
from .chart_widget import ChartWidget
from .table_widget import TableWidget
from .timeline_widget import TimelineWidget

__all__ = [
    "KPICard",
    "ChartWidget",
    "TableWidget",
    "TimelineWidget",
]
