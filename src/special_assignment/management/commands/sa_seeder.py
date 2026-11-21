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
from job.models import JobProxy
from manager.models import ManagerProxy
from special_assignment.models import SpecialAssignmentProxy


class Command(BaseCommand, CommandStdOutputMixin):
    help = _("Seed db with dummy special assignments")

    def add_arguments(self, parser):
        parser.add_argument(
            "--number",
            "-n",
            type=int,
            default=1,
            help=_("Number of seeded records"),
            required=False,
        )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                faker = Faker(locale="en_US")
                number = options.get("number")
                all_clients = ClientProxy.objects.all()
                all_jobs = JobProxy.objects.filter(
                    ~Q(status__in=[CON_ARCHIVED, CON_COMPLETED])
                ).order_by("?")[:100]
                all_users = BWUser.objects.filter(Q(is_active=True))
                all_jobs_lst = [job for job in all_jobs]
                all_clients_lst = [client for client in all_clients]
                all_clients_jobs_lst = all_jobs_lst + all_clients_lst
                all_bookkeepers = [
                    bookkeeper for bookkeeper in BookkeeperProxy.objects.all()
                ]
                all_managers = [manager for manager in ManagerProxy.objects.all()]
                all_assistants = [
                    assistant for assistant in AssistantProxy.objects.all()
                ]
                all_staff_users_lst = all_assistants + all_bookkeepers + all_managers

                for i in range(0, number, 1):
                    rand_main = random.choice(all_clients_jobs_lst)
                    rand_staff = random.choice(all_staff_users_lst)
                    fake_data = {
                        "client": None,
                        "job": None,
                        "assistant": None,
                        "bookkeeper": None,
                        "manager": None,
                        "is_seen": faker.pybool(),
                        "title": faker.job(),
                        "attachment": random.choice([faker.image_url(), None]),
                        "assigned_by": random.choice(all_users),
                        "body": faker.paragraph(nb_sentences=30),
                        "notes": faker.sentence(nb_words=15),
                        "status": random.choice(SpecialAssignmentStatusEnum.choices)[0],
                        "created_at": timezone.make_aware(
                            faker.date_time_between_dates(
                                datetime_start="-1y", datetime_end="now"
                            ),
                            timezone=timezone.get_current_timezone(),
                        ),
                        "start_date": faker.date_between(
                            # start_date="-1y", end_date="today"
                            start_date="-2d",
                            end_date="-1d",
                        ),
                        # "due_date": faker.date_between(start_date="-1y", end_date="today"),
                        "due_date": faker.date_between(
                            start_date="+4d", end_date="+5d"
                        ),
                    }
                    if isinstance(rand_main, JobProxy):
                        fake_data["job"] = rand_main
                    elif isinstance(rand_main, ClientProxy):
                        fake_data["client"] = rand_main
                    if isinstance(rand_staff, BookkeeperProxy):
                        fake_data["bookkeeper"] = rand_staff
                    elif isinstance(rand_staff, AssistantProxy):
                        fake_data["assistant"] = rand_staff
                    elif isinstance(rand_staff, ManagerProxy):
                        fake_data["manager"] = rand_staff
                    # debugging_print(fake_data)
                    sp_obj = SpecialAssignmentProxy.objects.create(**fake_data)
                    debugging_print(sp_obj)
                    debugging_print("################################")
        except Exception as ex:
            self.stdout_output("error", traceback.format_exc())
