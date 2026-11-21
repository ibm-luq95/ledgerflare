# -*- coding: utf-8 -*-#
import traceback

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from prettytable import PrettyTable
from django.db import transaction
from django.utils.translation import gettext as _

from core.constants.users import (
    ASSISTANT_GROUP_NAME,
    BOOKKEEPER_GROUP_NAME,
    DEFAULT_PERMISSIONS_NEW_STAFF_MEMBER,
    DEFAULT_READONLY_PERMISSIONS_NEW_STAFF_MEMBER,
    MANAGER_GROUP_NAME,
    READONLY_NEW_STAFF_MEMBER_GROUP_NAME,
)
from core.management.mixins import CommandStdOutputMixin
from core.utils import debugging_print


# from core.utils import debugging_print


class Command(BaseCommand, CommandStdOutputMixin):
    help = _(
        "Create groups for manager, bookkeeper, assistant, and default readonly for new"
        " staff member"
    )
    apps_name = ("manager", "bookkeeper", "assistant")
    groups_names = (
        BOOKKEEPER_GROUP_NAME,
        ASSISTANT_GROUP_NAME,
        MANAGER_GROUP_NAME,
        READONLY_NEW_STAFF_MEMBER_GROUP_NAME,
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-a",
            "--app-name",
            type=str,
            help=_("Pass app specific name to create group only"),
            required=False,
        )
        parser.add_argument(
            "--clear-all-groups",
            "-ca",
            nargs="?",
            action="store",
            const=True,
            type=str,
            required=False,
            help=_("Delete all groups for manager, bookkeeper, assistant"),
            # default=False,
        )
        parser.add_argument(
            "--list-all-groups",
            "-lg",
            nargs="?",
            action="store",
            const=True,
            type=str,
            required=False,
            help=_("List all groups in db"),
            # default=False,
        )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                passed_app = options.get("app_name")
                passed_clear = options.get("clear_all_groups")
                list_groups = options.get("list_all_groups")
                if list_groups:
                    table = PrettyTable()
                    table.field_names = ["ID", "Name", "Permissions Count"]
                    for group in Group.objects.all():
                        table.add_row([group.pk, group.name, group.permissions.count()])
                    print(table)
                    return
                # debugging_print(options)
                # debugging_print(passed_clear)
                if passed_clear:
                    self.clear_groups()
                    return
                if passed_app:
                    if passed_app not in self.apps_name:
                        raise Exception(
                            _(
                                f"The app {passed_app} not allowed!, the allowed"
                                f" {self.apps_name}"
                            )
                        )
                    models = [passed_app]
                else:
                    models = ["manager", "bookkeeper", "assistant"]

                for model in models:
                    group_obj = None
                    match model:
                        case "bookkeeper":
                            group_obj, created = Group.objects.get_or_create(
                                name=BOOKKEEPER_GROUP_NAME
                            )
                            content_type = ContentType.objects.get(
                                app_label="bookkeeper", model="Bookkeeper".lower()
                            )
                            # debugging_print(content_type)
                            bookkeeper_permission = Permission.objects.get(
                                codename="bookkeeper_user", content_type=content_type
                            )
                            group_obj.permissions.add(bookkeeper_permission)
                            group_obj.save()
                        case "assistant":
                            group_obj, created = Group.objects.get_or_create(
                                name=ASSISTANT_GROUP_NAME
                            )
                            content_type = ContentType.objects.get(
                                app_label="assistant", model="Assistant".lower()
                            )
                            # debugging_print(content_type)
                            assistant_permission = Permission.objects.get(
                                codename="assistant_user", content_type=content_type
                            )
                            group_obj.permissions.add(assistant_permission)
                            group_obj.save()
                        case "manager":
                            group_obj, created = Group.objects.get_or_create(
                                name=MANAGER_GROUP_NAME
                            )
                            content_type = ContentType.objects.get(
                                app_label="manager", model="Manager".lower()
                            )
                            # debugging_print(content_type)
                            manager_permission = Permission.objects.get(
                                codename="manager_user", content_type=content_type
                            )
                            group_obj.permissions.add(manager_permission)
                            group_obj.save()
                        case _:
                            raise Exception(_(f"The {model} not exists!"))

                    # debugging_print(group_obj.permissions.all())
                    self.stdout_output(
                        "success", _(f"Group {group_obj.name} created successfully")
                    )
                self.stdout_output(
                    "warn", _(f"Start creating read only new staff member group...")
                )
                readonly_group, created = Group.objects.get_or_create(
                    name=READONLY_NEW_STAFF_MEMBER_GROUP_NAME
                )
                if created:
                    self.stdout_output(
                        "warning",
                        _(f"Creating new group {READONLY_NEW_STAFF_MEMBER_GROUP_NAME}"),
                    )
                else:
                    self.stdout_output(
                        "warn",
                        _(
                            f"The group {READONLY_NEW_STAFF_MEMBER_GROUP_NAME} is"
                            " already exists"
                        ),
                    )
                for content_type_item in DEFAULT_READONLY_PERMISSIONS_NEW_STAFF_MEMBER:
                    content_type_object = ContentType.objects.get(
                        app_label=content_type_item["app_label"],
                        model=content_type_item["model_label"],
                    )
                    permissions_codename_labels = content_type_item.get(
                        "permissions_codename_labels"
                    )
                    permissions_codename_list_objs = []
                    for codename in permissions_codename_labels:
                        permission_object = Permission.objects.get(
                            codename=codename, content_type=content_type_object
                        )
                        permissions_codename_list_objs.append(permission_object)
                    readonly_group.permissions.add(*permissions_codename_list_objs)
                    readonly_group.save()
                self.stdout_output(
                    "success",
                    _(
                        f"The group {READONLY_NEW_STAFF_MEMBER_GROUP_NAME} created"
                        " successfully!"
                    ),
                )
        except Exception as ex:
            print(traceback.format_exc())
            self.stdout_output("error", str(ex))

    def clear_groups(self):
        try:
            with transaction.atomic():
                for group in self.groups_names:
                    group_obj = Group.objects.filter(name=group)
                    if group_obj.count() <= 0:
                        self.stdout_output("error", _(f"Group {group} not exists!"))
                        pass
                    else:
                        group_obj = group_obj.first()
                        self.stdout_output("warn", _(f"Deleting {group}"))
                        group_obj.delete()

        except Exception as ex:
            self.stdout_output("error", str(ex))
