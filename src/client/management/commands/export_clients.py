from django.utils.translation import gettext as _

from client.resources.client import ClientResource
from core.management.mixins.export_mixin import ExportingCommandMixin


class Command(ExportingCommandMixin):
    def __init__(self,  *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.resources_object = ClientResource()
        self.app_name = "client"
        self.file_name = "ClientProxy"
        self.help = _("Export clients for backup")
