from __future__ import annotations

from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from lf_notifications.models import NotificationRecipientProxy

class NotificationListView(LoginRequiredMixin, ListView):
    model = NotificationRecipientProxy
    template_name = "lf_notifications/list.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        qs = NotificationRecipientProxy.objects.filter(
            recipient=self.request.user
        ).select_related(
            "notification", 
            "notification__actor", 
            "notification__content_type"
        ).prefetch_related(
            "notification__actor__bookkeeper__profile",
            "notification__actor__manager__profile",
            "notification__actor__assistant__profile",
            "notification__actor__cfo__profile",
        ).order_by("-created_at")

        filter_param = self.request.GET.get("filter")
        if filter_param == "unread":
            qs = qs.filter(is_read=False)
        elif filter_param == "discussion":
            qs = qs.filter(notification__content_type__model__in=["discussion", "discussionproxy"])
        elif filter_param == "job":
            qs = qs.filter(notification__content_type__model__in=["job", "jobproxy", "specialassignment", "specialassignmentproxy"])

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_qs = NotificationRecipientProxy.objects.filter(recipient=self.request.user)
        context["unread_count"] = base_qs.filter(is_read=False).count()
        context["total_count"] = base_qs.count()
        context["current_filter"] = self.request.GET.get("filter", "all")
        return context
