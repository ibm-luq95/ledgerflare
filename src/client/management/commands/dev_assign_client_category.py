import random
import traceback

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import gettext as _

from client.models import ClientProxy
from client_category.models import ClientCategory
from core.management.mixins import CommandStdOutputMixin


class Command(BaseCommand, CommandStdOutputMixin):
    help = _("Assign client category")

    def add_arguments(self, parser):
        parser.add_argument(
            "--assign-category-to-clients",
            "-acc",
            const=True,
            nargs="?",
            type=bool,
            help=_("Assign category to clients"),
            required=True,
            action="store",
        )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                assign_category_to_clients = options.get("assign_category_to_clients")
                if assign_category_to_clients:
                    all_categories = ClientCategory.objects.all()
                    all_clients = ClientProxy.objects.all()
                    for client in all_clients:
                        rands_cats = random.choices(all_categories, k=3)
                        client.categories.add(*rands_cats)
                        client.save()

                    # for client in all_clients:
                    #     debugging_print(client.categories.all())
                    #     debugging_print("#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        except Exception:
            self.stdout_output("error", traceback.format_exc())
