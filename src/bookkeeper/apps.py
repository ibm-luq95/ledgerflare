from django.apps import AppConfig


class BookkeeperConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bookkeeper"

    def ready(self):
        import bookkeeper.signals.handlers  # noqa: F401
