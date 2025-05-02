# -*- coding: utf-8 -*-#
import traceback

from django.contrib.auth.models import Permission
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from assistant.models import AssistantProxy
from core.constants.users import ASSISTANT_FULL_MANAGER_PERMISSION_SHORT_NAME
from core.utils import get_formatted_logger, colored_output_with_logging

# TODO: remove the custom logger before push (only for development)
# ###### [Custom Logger] #########
logger = get_formatted_logger()


# ###### [Custom Logger] #########
@receiver(post_save, sender=AssistantProxy)
def assign_manager_permission(sender, instance: AssistantProxy, created: bool, **kwargs):
    try:
        if created is True:
            with transaction.atomic():
                # assign manager permission to assistant
                manager_perm = Permission.objects.get(
                    codename=ASSISTANT_FULL_MANAGER_PERMISSION_SHORT_NAME
                )
                # debugging_print(manager_perm)
                if instance.assistant_type == "admin":
                    instance.user.user_permissions.add(manager_perm)

                else:
                    instance.user.user_permissions.remove(manager_perm)

                instance.user.save()
    except Exception as ex:
        colored_output_with_logging(
            is_logged=True, text=traceback.format_exc(), log_level="error", color="red"
        )
        raise Exception(str(ex))
