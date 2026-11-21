from django.contrib import admin

from core.admin import BWBaseAdminModelMixin
from core.utils.developments.debugging_print_object import DebuggingPrint
from important_contact.models import ImportantContact


@admin.register(ImportantContact)
class ImportantContactAdmin(BWBaseAdminModelMixin):
    list_display = [
        "get_client",
        "contact_label",
        "company_name",
        "contact_first_name",
        "contact_last_name",
        "created_at",
    ]

    @admin.display(description="Client")
    def get_client(self, obj: ImportantContact):
        # DebuggingPrint.print(obj.client.all())
        return obj.client
