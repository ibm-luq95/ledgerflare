import json

from easyaudit.models import CRUDEvent

from core.utils import get_formatted_logger

logger = get_formatted_logger()


class CRUDEventProxy(CRUDEvent):
    """
    CRUDEventProxy is a proxy model that extends the CRUDEvent model.

    This class provides additional functionality to check if a CRUDEvent instance is a custom delete or update event.

    Attributes:
        is_custom_deleted (bool | None): A property that checks if the CRUDEvent instance is a custom delete event.
            Returns True if the event is a custom delete event, False if it is not, and None if there was an error.
        is_custom_update (bool | None): A property that checks if the CRUDEvent instance is a custom update event.
            Returns True if the event is a custom update event, False if it is not, and None if there was an error.

    """

    class Meta:
        proxy = True

    @property
    def is_custom_deleted(self) -> bool | None:
        """
        Checks if the CRUDEvent instance is a custom delete event.

        Returns:
            bool | None: True if the event is a custom delete event, False if it is not, and None if there was an error.

        """
        try:
            if self.is_update() is True:
                changed_fields_json = json.loads(self.changed_fields)
                if changed_fields_json:
                    if "is_deleted" in list(changed_fields_json.keys()):
                        if changed_fields_json.get("is_deleted")[1] == "True":
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
        """
        Checks if the CRUDEvent instance is a custom update event.

        Returns:
            bool | None: True if the event is a custom update event, False if it is not, and None if there was an error.

        """
        try:
            if self.is_update() is True:
                changed_fields_json = json.loads(self.changed_fields)
                if changed_fields_json:
                    if "is_deleted" not in list(changed_fields_json.keys()):
                        return True
                    else:
                        return False
        except Exception as ex:
            logger.error(str(ex))
            return None
