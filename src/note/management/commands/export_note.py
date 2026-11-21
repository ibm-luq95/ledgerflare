from django.utils.translation import gettext as _

from core.management.mixins.export_mixin import ExportingCommandMixin
from note.resources.note import NoteResource


class Command(ExportingCommandMixin):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.resources_object = NoteResource()
        self.app_name = "note"
        self.file_name = "Note"
        self.help = _("Export notes for backup")
