# -*- coding: utf-8 -*-#
import random
import traceback

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _
from faker import Faker

from assistant.models import AssistantProxy
from beach_wood_user.models import BWUser
from bookkeeper.models import BookkeeperProxy
from client.models import ClientProxy
from core.choices.special_assignment import SpecialAssignmentStatusEnum
from core.constants.status_labels import CON_ARCHIVED, CON_COMPLETED
from core.management.mixins import CommandStdOutputMixin
from core.utils import debugging_print
from core.utils.developments.debugging_print_object import DebuggingPrint
from core.utils.developments.debugging_prompt import DebuggingPrompt
from job.models import JobProxy
from manager.models import ManagerProxy
from special_assignment.models import SpecialAssignmentProxy


class Command(BaseCommand, CommandStdOutputMixin):
    help = _("Fix special assignments associated with users")

    # def add_arguments(self, parser):
    #     parser.add_argument(
    #         "--number",
    #         "-n",
    #         type=int,
    #         default=1,
    #         help=_("Number of seeded records"),
    #         required=False,
    #     )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                ask = DebuggingPrompt.confirm(
                    "Do you want to start fixing special assignments? [y/n]"
                )
                if ask is False:
                    DebuggingPrint.print("[yellow bold]Quitting...")
                    return
                else:
                    DebuggingPrint.pprint(_("Fixing special assignments..."))
                    all_special_assignments = SpecialAssignmentProxy.objects.all()
                    for special_assignment in all_special_assignments:
                        if not special_assignment.assigned_to:
                            if special_assignment.get_managed_user():

                                DebuggingPrint.pprint(
                                    special_assignment.get_managed_user().user
                                )
                                special_assignment.assigned_to = (
                                    special_assignment.get_managed_user().user
                                )
                                special_assignment.save()
                                DebuggingPrint.print(
                                    f"Special assignment {special_assignment} assigned to {special_assignment.assigned_to}"
                                )

                            else:
                                DebuggingPrint.pprint("No user")
                        else:
                            DebuggingPrint.pprint("[yellow bold]Already assigned")

        except Exception as ex:
            self.stdout_output("error", traceback.format_exc())
