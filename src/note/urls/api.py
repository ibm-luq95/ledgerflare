
from rest_framework import routers

from note.views import NoteViewSet


app_name = "api"

router = routers.DefaultRouter()
router.register(r"notes-api", NoteViewSet, basename="note-api-router")

urlpatterns = router.urls
