from import_export import resources

from important_contact.models import ImportantContact


class ImportantContactResource(resources.ModelResource):
    class Meta:
        model = ImportantContact
