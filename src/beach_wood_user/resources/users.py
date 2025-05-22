# -*- coding: utf-8 -*-#
from import_export import resources

from beach_wood_user.models import BWUser
from core.utils.developments.debugging_print_object import DebuggingPrint


class UsersResource(resources.ModelResource):
    class Meta:
        model = BWUser

    # def before_import(self, dataset, **kwargs):
    #     DebuggingPrint.pprint(dataset)
    #     DebuggingPrint.pprint(kwargs)
    #     print("Preparing to import data...")


    # def after_import(self, dataset, result, **kwargs):
    #     # Custom logic after import
    #     print("Import completed.")
    #
    # def import_row(self, row, instance_loader, **kwargs):
    #     DebuggingPrint.pprint(row)
    #     DebuggingPrint.pprint(instance_loader)
    #     DebuggingPrint.pprint(kwargs)
    #     return super().import_row(row, instance_loader, **kwargs)
