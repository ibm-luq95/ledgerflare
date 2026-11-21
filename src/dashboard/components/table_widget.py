"""
Table Widget Component

A reusable table component for displaying data with optional sorting,
pagination, and action buttons.
"""

from django_components import Component
from django_components import register


@register("lf_table_widget")
class TableWidget(Component):
    """
    Table Widget component for displaying tabular data.

    Usage:
        {% lf_table_widget
           title="Past Due Jobs"
           columns=columns
           rows=rows
           empty_message="No past due jobs"
           loading=True %}
    """

    template_name = "dashboard/components/widgets/table_widget/table_widget.html"

    class Cache:
        enabled = False

    def get_context_data(
        self,
        title,
        columns=None,
        rows=None,
        empty_message=None,
        link_url=None,
        link_text="View All",
        loading=False,
        widget_name=None,
        element_id=None,
        show_row_numbers=False,
        hoverable=True,
    ):
        return {
            "title": title,
            "columns": columns or [],
            "rows": rows or [],
            "empty_message": empty_message or "No data available",
            "link_url": link_url,
            "link_text": link_text,
            "loading": loading,
            "widget_name": widget_name,
            "element_id": element_id,
            "show_row_numbers": show_row_numbers,
            "hoverable": hoverable,
        }

    class Media:
        # No additional CSS/JS needed - uses existing Tailwind classes
        pass
