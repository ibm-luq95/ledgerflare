from import_export import resources

from client.models import ClientProxy


class ClientResource(resources.ModelResource):
    class Meta:
        model = ClientProxy
