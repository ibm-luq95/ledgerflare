from django.apps import AppConfig


class DiscussionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "discussion"

    def ready(self):
        import discussion.signals.notification  # noqa
