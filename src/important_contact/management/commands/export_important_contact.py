from django.utils.translation import gettext as _

from core.management.mixins.export_mixin import ExportingCommandMixin
from important_contact.resources.important_contact import ImportantContactResource


class Command(ExportingCommandMixin):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.resources_object = ImportantContactResource()
        self.app_name = "important contact"
        self.file_name = "ImportantContact"
        self.help = _("Export important contact for backup")
