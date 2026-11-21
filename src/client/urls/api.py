
from django.urls import path
from rest_framework import routers

from client.views.api import ClientDropdownView, ClientViewSet


app_name = "api"

router = routers.DefaultRouter()
router.register(r"client-api", ClientViewSet, basename="client-api-router")

urlpatterns = router.urls + [
    path("dropdown/", ClientDropdownView.as_view(), name="dropdown"),
]
