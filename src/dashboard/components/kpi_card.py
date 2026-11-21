"""
KPI Card Component

A reusable KPI (Key Performance Indicator) card component for displaying metrics
with optional alert styling, trend indicators, and links.
"""

from django_components import Component
from django_components import register


@register("lf_kpi_card")
class KPICard(Component):
    """
    KPI Card component for displaying metrics.

    Usage:
        {% lf_kpi_card
           title="Past Due Jobs"
           value=0
           icon="fa-triangle-exclamation"
           alert=True
           widget_name="past_due_jobs"
           element_id="lfPastDueJobs" %}
    """

    template_name = "dashboard/components/widgets/kpi_card/kpi_card.html"

    class Cache:
        enabled = False

    def get_context_data(
        self,
        title,
        value=0,
        icon="fa-chart-simple",
        link_url=None,
        alert=False,
        trend=None,
        trend_positive=True,
        loading=False,
        widget_name=None,
        element_id=None,
        color="blue",
    ):
        return {
            "title": title,
            "value": value,
            "icon": icon,
            "link_url": link_url,
            "alert": alert,
            "trend": trend,
            "trend_positive": trend_positive,
            "loading": loading,
            "widget_name": widget_name,
            "element_id": element_id,
            "color": color,
        }
