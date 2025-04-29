# -*- coding: utf-8 -*-#
from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext as _

from bookkeeper.models import BookkeeperProxy
from core.admin import BWBaseAdminModelMixin
from core.utils.developments.debugging_print_object import DebuggingPrint


@admin.register(BookkeeperProxy)
class BookkeeperAdmin(BWBaseAdminModelMixin):
    # list_filter = [] + BWBaseAdminModelMixin.list_filter
    list_display = ["user", "user__email", "is_deleted", "user_is_deleted", "created_at"]
    actions = ["fix_delete_issue"]

    def user_is_deleted(self, obj):
        # Safely access the related User's is_deleted field
        return obj.user.is_deleted if obj.user else False

    user_is_deleted.boolean = True  # Enables check/X icons
    user_is_deleted.short_description = "User Deleted"  # Column header label

    @admin.action(description=_("Fix delete issue"))
    def fix_delete_issue(self, request: HttpRequest, queryset: QuerySet[BookkeeperProxy]):
        try:

            if queryset:
                emails_list: set[str] = set()
                for bookkeeper in queryset:
                    if (
                        bookkeeper.is_deleted is True
                        and bookkeeper.user.is_deleted is False
                    ):
                        DebuggingPrint.pprint(
                            f"Bookkeeper: {bookkeeper} not deleted correctly"
                        )
                        emails_list.add(bookkeeper.user.email)
                        bookkeeper.user.delete()
                        # self.message_user(
                        #     request,
                        #     f"Bookkeeper: {bookkeeper} not deleted correctly",
                        #     level=messages.WARNING,
                        # )
                    elif (
                        bookkeeper.user.is_deleted is True
                        and bookkeeper.is_deleted is False
                    ):
                        emails_list.add(bookkeeper.user.email)
                        bookkeeper.delete()

                    else:
                        self.message_user(
                            request,
                            f"Bookkeeper: {bookkeeper} deleted correctly",
                            level=messages.INFO,
                        )
                        DebuggingPrint.pprint(
                            f"Bookkeeper: {bookkeeper} deleted correctly"
                        )

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
