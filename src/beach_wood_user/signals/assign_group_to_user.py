# -*- coding: utf-8 -*-#
import traceback

from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext as _

from assistant.models import AssistantProxy, Assistant
from beach_wood_user.helpers.permission_helper import PermissionHelper
from beach_wood_user.models import Profile
from beach_wood_user.models.beach_wood_user import BWUser
from bookkeeper.models import BookkeeperProxy, Bookkeeper
from cfo.models import CFOProxy, CFO
from core.constants.status_labels import CON_ENABLED
from core.constants.users import (
    BOOKKEEPER_GROUP_NAME,
    MANAGER_GROUP_NAME,
    ASSISTANT_GROUP_NAME,
    READONLY_NEW_STAFF_MEMBER_GROUP_NAME,
)
from core.utils import get_formatted_logger, debugging_print, colored_output_with_logging
from core.utils.developments.debugging_print_object import DebuggingPrint
from manager.models import ManagerProxy, Manager
from staff_briefcase.models import StaffBriefcase

# TODO: remove the custom logger before push (only for development)
# ###### [Custom Logger] #########
logger = get_formatted_logger()


# ###### [Custom Logger] #########


@receiver(post_save, sender=BWUser)
def assign_groups(sender, instance: BWUser, created: bool, **kwargs):
    try:
        if created:
            created_user = instance
            DebuggingPrint.pprint(instance)
            user_type = created_user.user_type

            with transaction.atomic():
                match user_type:
                    case "assistant":
                        group = ASSISTANT_GROUP_NAME
                        permission_codename = "assistant_user"
                        assistant = Assistant.objects.create(
                            user=created_user, profile=Profile.objects.create()
                        )
                        # # Create profile for new user
                        # assistant.profile = Profile()
                        # assistant.save()
                    case "bookkeeper":
                        group = BOOKKEEPER_GROUP_NAME
                        permission_codename = "bookkeeper_user"
                        bookkeeper = Bookkeeper.objects.create(
                            user=created_user, profile=Profile.objects.create()
                        )
                        # # Create profile for new user
                        # bookkeeper.profile = Profile()
                        # bookkeeper.save()
                    case "manager":
                        group = MANAGER_GROUP_NAME
                        permission_codename = "manager_user"
                        manager = Manager.objects.create(
                            user=created_user, profile=Profile.objects.create()
                        )
                    case "cfo":
                        cfo = CFO.objects.create(
                            user=created_user, profile=Profile.objects.create()
                        )
                        # print("DDDDD")
                        # print(cfo.pro)
                readonly_group = Group.objects.filter(
                    name=READONLY_NEW_STAFF_MEMBER_GROUP_NAME
                )
                # if readonly_group:
                #     readonly_group = readonly_group.first()
                # if (
                #     created_user.user_type == "bookkeeper"
                #     or created_user.user_type == "assistant"
                # ):
                #     created_user.groups.add(readonly_group)
                if created_user.user_type == "bookkeeper":
                    group_obj = Group.objects.get(name=BOOKKEEPER_GROUP_NAME)
                    created_user.groups.add(group_obj)
                if created_user.user_type == "assistant":
                    group_obj = Group.objects.get(name=ASSISTANT_GROUP_NAME)
                    created_user.groups.add(group_obj)
                if created_user.user_type == "manager":
                    group_obj = Group.objects.get(name=MANAGER_GROUP_NAME)
                    created_user.groups.add(group_obj)
                permissions_list = PermissionHelper.get_bw_default_permissions(
                    as_list=True
                )
                created_user.user_permissions.add(*permissions_list)
                if created_user.status == CON_ENABLED:
                    created_user.is_active = True
                else:
                    created_user.is_active = False
                briefcase = StaffBriefcase.objects.create(user=created_user)
                created_user.save()

    except Exception as ex:
        colored_output_with_logging(
            is_logged=True, text=traceback.format_exc(), log_level="error", color="red"
        )
        raise Exception(str(ex))
