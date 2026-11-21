from __future__ import annotations

from rest_framework import routers
from lf_notifications.views.notification import NotificationViewSet

router = routers.DefaultRouter()
router.register(r"notifications", NotificationViewSet, basename="notifications")

urlpatterns = router.urls
