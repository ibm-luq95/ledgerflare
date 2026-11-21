
from rest_framework import routers

from task.views import TaskViewSet


app_name = "api"

router = routers.DefaultRouter()
router.register(r"task-api", TaskViewSet, basename="task-api-router")

urlpatterns = router.urls
