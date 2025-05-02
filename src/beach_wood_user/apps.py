from django.apps import AppConfig


class BeachWoodUserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "beach_wood_user"
    verbose_name = "Beach Wood Users"

    def ready(self) -> None:
        # Signal.disconnect(update_last_login, sender=get_user_model())
        # import beach_wood_user.signals.login
        import beach_wood_user.signals.assign_group_to_user
        # import beach_wood_user.signals.delete_user
        import beach_wood_user.signals.handlers
