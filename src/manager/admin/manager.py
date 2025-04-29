# -*- coding: utf-8 -*-#
from django.contrib import admin, messages
from django.utils.translation import gettext as _

from django.db.models import QuerySet
from django.http import HttpRequest

from core.utils.developments.debugging_print_object import DebuggingPrint
from manager.models import ManagerProxy
from core.admin import BWBaseAdminModelMixin


@admin.register(ManagerProxy)
class ManagerAdmin(BWBaseAdminModelMixin):
    list_filter = [] + BWBaseAdminModelMixin.list_filter
    list_display = [
        "user",
        "user__email",
        "is_deleted",
        "user_is_deleted",
        "created_at",
    ]

    actions = ["fix_delete_issue"]

    def user_is_deleted(self, obj):
        # Safely access the related User's is_deleted field
        return obj.user.is_deleted if obj.user else False

    user_is_deleted.boolean = True  # Enables check/X icons
    user_is_deleted.short_description = "User Deleted"  # Column header label

    @admin.action(description=_("Fix delete issue"))
    def fix_delete_issue(self, request: HttpRequest, queryset: QuerySet[ManagerProxy]):
        try:

            if queryset:
                emails_list: set[str] = set()
                for manager in queryset:
                    if manager.is_deleted is True and manager.user.is_deleted is False:
                        DebuggingPrint.pprint(f"Manager: {manager} not deleted correctly")
                        emails_list.add(manager.user.email)
                        manager.user.delete()
                        # self.message_user(
                        #     request,
                        #     f"Manager: {manager} not deleted correctly",
                        #     level=messages.WARNING,
                        # )
                    elif manager.user.is_deleted is True and manager.is_deleted is False:
                        emails_list.add(manager.user.email)
                        manager.delete()

                    else:
                        self.message_user(
                            request,
                            f"Manager: {manager} deleted correctly",
                            level=messages.INFO,
                        )
                        DebuggingPrint.pprint(f"Manager: {manager} deleted correctly")

                if emails_list:
                    self.message_user(
                        request,
                        f"Users with issues: {', '.join(emails_list)} fixed successfully",
                        level=messages.SUCCESS,
                    )

            else:
                self.message_user(
                    request,
                    _("Please select users to fix delete issue"),
                    level=messages.ERROR,
                )
        except Exception as ex:
            self.message_user(request, str(ex), level=messages.ERROR)
