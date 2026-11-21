"""
Chart Widget Component

A reusable Chart.js wrapper component for displaying various chart types
with loading states and empty state handling.
"""

from django_components import Component
from django_components import register


@register("lf_chart_widget")
class ChartWidget(Component):
    """
    Chart Widget component for displaying Chart.js charts.

    Usage:
        {% lf_chart_widget
           title="Staff Workload Distribution"
           chart_id="lfStaffWorkloadChart"
           chart_type="bar"
           loading=True %}
    """

    template_name = "dashboard/components/widgets/chart_widget/chart_widget.html"

    class Cache:
        enabled = False

    def get_context_data(
        self,
        title,
        chart_id,
        chart_type="doughnut",
        loading=False,
        empty_message=None,
        wrapper_classes="",
        height="h-48",
    ):
        return {
            "title": title,
            "chart_id": chart_id,
            "chart_type": chart_type,
            "loading": loading,
            "empty_message": empty_message or "No data available",
            "wrapper_classes": wrapper_classes,
            "height": height,
        }

    class Media:
        # Chart.js should be loaded globally in the base template
        pass
