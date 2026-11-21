"""
Timeline Widget Component

A reusable timeline component for displaying activity feeds, assignments,
and other chronological events.
"""

from django_components import Component
from django_components import register


@register("lf_timeline_widget")
class TimelineWidget(Component):
    """
    Timeline Widget component for displaying chronological events.

    Usage:
        {% lf_timeline_widget
           title="Recent Activity"
           items=items
           empty_message="No recent activity"
           loading=True %}
    """

    template_name = "dashboard/components/widgets/timeline_widget/timeline_widget.html"

    class Cache:
        enabled = False

    def get_context_data(
        self,
        title,
        items,
        item_template,
        empty_message,
        link_url,
        link_text,
        loading,
        widget_name,
        element_id,
        show_dates,
    ):
        return {
            "title": title,
            "items": items or [],
            "item_template": item_template,
            "empty_message": empty_message or "No recent activity",
            "link_url": link_url,
            "link_text": link_text,
            "loading": loading,
            "widget_name": widget_name,
            "element_id": element_id,
            "show_dates": show_dates,
        }

    class Media:
        # No additional CSS/JS needed - uses existing Tailwind classes
        pass
