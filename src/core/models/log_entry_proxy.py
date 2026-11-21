from __future__ import annotations

from typing import Any

from auditlog.models import LogEntry

from core.utils import get_formatted_logger

logger = get_formatted_logger()


class LogEntryProxy(LogEntry):

    class Meta:
        proxy = True

    @property
    def datetime(self) -> Any:
        return self.timestamp

    @property
    def user(self) -> Any:
        return self.actor

    def get_event_type_display(self) -> str:
        if self.action == self.Action.CREATE:
            return "Create"
        elif self.action == self.Action.UPDATE:
            if self.changes:
                for val in self.changes.values():
                    if isinstance(val, dict) and val.get("type") == "m2m":
                        if val.get("operation") == "add":
                            return "Many-to-Many Add"
                        elif val.get("operation") == "delete":
                            return "Many-to-Many Remove"
            return "Update"
        elif self.action == self.Action.DELETE:
            return "Delete"
        return "Unknown"

    @property
    def is_custom_deleted(self) -> bool | None:
        try:
            if self.action == self.Action.UPDATE:
                changes = self.changes
                if changes and "is_deleted" in changes:
                    val = changes.get("is_deleted")[1]
                    if val is True or val == "True":
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return None
        except Exception as ex:
            logger.error(str(ex))
            return None

    @property
    def is_custom_update(self) -> bool | None:
        try:
            if self.action == self.Action.UPDATE:
                changes = self.changes
                if changes:
                    if "is_deleted" not in changes:
                        return True
                    else:
                        return False
            return False
        except Exception as ex:
            logger.error(str(ex))
            return None
