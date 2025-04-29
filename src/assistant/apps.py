from django.apps import AppConfig


class AssistantConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "assistant"

    def ready(self) -> None:
        import assistant.signals.assign_manager_permission
        import assistant.signals.handlers
