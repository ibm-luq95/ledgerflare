from django.apps import AppConfig


class CfoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cfo"

    def ready(self):
        import cfo.signals.handlers
