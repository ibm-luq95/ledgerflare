from rest_framework import routers

from important_contact.views import ImportantContactViewSet


app_name = "api"

router = routers.DefaultRouter()
router.register(
    r"important-contacts-api", ImportantContactViewSet, basename="contacts-api-router"
)

urlpatterns = router.urls
