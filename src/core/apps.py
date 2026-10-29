"""Core application configuration and auditlog registrations."""

from __future__ import annotations

import re

from django.apps import AppConfig
from django.utils import cache as django_cache


django_cache.cc_delim_re = re.compile(r"\s*,\s*")


class CoreConfig(AppConfig):
    """Core application config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self) -> None:
        """Register models with auditlog and initialize signal receivers."""
        from auditlog.registry import auditlog
        from django.apps import apps

        import core.signals.auditlog

        auditlog.register(apps.get_model("beach_wood_user", "BWUser"))
        auditlog.register(apps.get_model("client", "Client"))
        auditlog.register(apps.get_model("job", "Job"))
        auditlog.register(apps.get_model("task", "Task"))
        auditlog.register(apps.get_model("document", "Document"))
        auditlog.register(apps.get_model("note", "Note"))
        auditlog.register(apps.get_model("special_assignment", "SpecialAssignment"))

        auditlog.register(apps.get_model("client", "ClientProxy"))
        auditlog.register(apps.get_model("job", "JobProxy"))
        auditlog.register(apps.get_model("task", "TaskProxy"))
        auditlog.register(
            apps.get_model("special_assignment", "SpecialAssignmentProxy")
        )
        auditlog.register(apps.get_model("assistant", "AssistantProxy"))
        auditlog.register(apps.get_model("bookkeeper", "BookkeeperProxy"))
        auditlog.register(apps.get_model("manager", "ManagerProxy"))
