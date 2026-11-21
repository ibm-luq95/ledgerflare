# -*- coding: utf-8 -*-#
import traceback
import random

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.timezone import datetime, make_aware
from django.db import transaction

from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _

from beach_wood_user.models import BWUser
from core.choices import JobTypeEnum, JobStateEnum, JobStatusEnum
from core.management.mixins import CommandStdOutputMixin

from faker import Faker
from client.models import ClientProxy
from core.utils import debugging_print
from job.models import JobProxy
from job_category.models import JobCategory


class Command(BaseCommand, CommandStdOutputMixin):
    help = _("Jobs seeder")

    def add_arguments(self, parser):
        parser.add_argument(
            "--number",
            "-n",
            type=int,
            help=_("Number of records"),
            required=False,
            default=1,
        )
        parser.add_argument(
            "--client", "-c", type=str, help=_("Client"), required=False
        )
        parser.add_argument(
            "--created-year", "-cy", type=int, help=_("Created year"), required=False
        )
        # parser.add_argument(
        #     "--",
        #     "-",
        #     nargs="?",
        #     action="store",
        #     const=True,
        #     type=str,
        #     required=False,
        #     help=_(""),
        #     # default=False,
        # )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                number = options.get("number")
                client = options.get("client")
                created_year = options.get("created_year")
                # seeder = Seed.seeder("en_US")
                faker = Faker(locale="en_US")
                all_clients = ClientProxy.objects.all()
                all_job_categories = JobCategory.objects.all()
                all_users = BWUser.objects.all()
                if client is not None:
                    self.stdout_output("warn", _(f"Seed jobs for client {client}"))
                for i in range(0, number, 1):
                    fake_data = {
                        # "client": random.choice(all_clients),
                        # "managed_by": random.choice(all_users),
                        "title": faker.job(),
                        "description": faker.paragraph(nb_sentences=30),
                        "note": faker.sentence(nb_words=15),
                        "job_type": random.choice(JobTypeEnum.choices)[0],
                        "state": random.choice(JobStateEnum.choices)[0],
                        "status": random.choice(JobStatusEnum.choices)[0],
                        "created_at": timezone.make_aware(
                            faker.date_time_between_dates(
                                datetime_start="-6m", datetime_end="now"
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
                    if client is not None:
                        fake_data["client"] = ClientProxy.objects.get(pk=client)
                    else:
                        fake_data["client"] = random.choice(all_clients)
                    client_bookkeepers = fake_data["client"].bookkeepers.all()
                    if client_bookkeepers:
                        bookkeepers_users = [
                            bookkeeper.user for bookkeeper in client_bookkeepers
                        ]
                        fake_data["managed_by"] = random.choice(bookkeepers_users)
                    new_job = JobProxy.objects.create(**fake_data)
                    cats = random.sample(list(all_job_categories), 2)
                    new_job.categories.add(*cats)
                    # debugging_print(new_job.categories.all())
                    new_job.save()
                    debugging_print(f"{new_job.title} - created successfully!")

        except Exception as ex:
            self.stdout_output("error", traceback.format_exc())
