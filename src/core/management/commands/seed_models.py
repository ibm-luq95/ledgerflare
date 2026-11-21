# -*- coding: utf-8 -*-#
from django.core.management.base import BaseCommand
from django.apps import apps
from django.contrib.sites.models import Site
from collections import defaultdict
from faker import Faker
from faker.providers import internet, job, lorem, person, color, address, bank, company
import random
from django.db import transaction

from core.choices import JobStatusEnum, JobTypeEnum, JobStateEnum
from job.models import JobProxy
from job_category.models import JobCategory
from client.models import ClientProxy
from client_category.models import ClientCategory
from discussion.models import DiscussionProxy
from special_assignment.models import SpecialAssignmentProxy

# import colorama
from colorama import Fore

from core.management.mixins import CommandStdOutputMixin, ProductionGuardCommandMixin
from core.utils import debugging_print
from beach_wood_user.models import BWUser

apps_maps = defaultdict(list)
for model in apps.get_models():
    # apps_maps.setdefault(model._meta.app_label, model._meta.object_name)
    apps_maps[model._meta.app_label].append(model._meta.object_name)


class Command(ProductionGuardCommandMixin, CommandStdOutputMixin, BaseCommand):
    help = "Seed django model with fake data"
    # _APPS_MAP = sorted(apps_maps.items())
    _APPS_MAP = apps_maps
    _MODELS = {
        "job": JobProxy,
        "job_category": JobCategory,
        "discussion": DiscussionProxy,
        "client": ClientProxy,
        "client_category": ClientCategory,
        "special_assignment": SpecialAssignmentProxy,
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "-m",
            "--model-name",
            type=str,
            help="Pass app specific name to seed data",
            required=True,
            action="append",
        )
        parser.add_argument(
            "-c", "--count", type=int, help="Fake data count", required=False, default=10
        )

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # debugging_print(options)
                models_list = options.get("model_name")
                count = options.get("count")
                fake = Faker()
                kk = ["onw", "sdjkf", 77]
                f = fake.random_element(kk)
                # debugging_print(f)
                # debugging_print(fake.random_element, is_inspect=True, help=True)
                # debugging_print(fake.randomize_nb_elements, is_inspect=True, help=True)
                # print(fake.random_element.__doc__)
                # debugging_print(len(dir(fake)))
                fake.add_provider(internet)
                fake.add_provider(person)
                fake.add_provider(job)
                fake.add_provider(lorem)
                fake.add_provider(company)
                fake.add_provider(bank)
                fake.add_provider(address)
                fake.add_provider(color)
                # debugging_print(len(dir(fake)))
                # debugging_print(dir(fake))
                models_iter = iter(models_list)
                job_status = [j[0] for j in JobStatusEnum.choices]
                job_types = [j[0] for j in JobTypeEnum.choices]
                job_states = [j[0] for j in JobStateEnum.choices]
                job_categories = [j for j in JobCategory.objects.all()]
                for i in range(0, len(models_list)):
                    current_model = next(models_iter)
                    for j in range(0, count):
                        # debugging_print(current_model)
                        match current_model:
                            case "job":
                                created_data = {
                                    "client": ClientProxy.objects.random(),
                                    "title": f"Gen - {fake.text(max_nb_chars=30)}",
                                    "description": f"Gen - {fake.text(max_nb_chars=200)}",
                                    "is_created_from_template": False,
                                    "note": f"Gen - {fake.text(max_nb_chars=20)}",
                                    "job_type": random.choice(job_types),
                                    "status": random.choice(job_status),
                                    "state": random.choice(job_states),
                                    "managed_by": CustomUser.objects.random(),
                                }
                                job_categories = fake.random_choices(
                                    elements=job_categories
                                )
                                job_obj = JobProxy.objects.create(**created_data)
                                job_obj.categories.add(*job_categories)
                                job_obj.save()
                                debugging_print(f"Created job - {job_obj.title}")
                            case "discussion":
                                random_job = random.choice(
                                    list(JobProxy.objects.all()) + [None, None, None]
                                )
                                # random_special_assignment = random.choice(
                                #     list(SpecialAssignment.objects.all()) + [None]
                                # )
                                random_special_assignment = random.choice(
                                    list(SpecialAssignment.objects.all())
                                )
                                created_data = {
                                    "job": random_job,
                                    "body": f"Gen - {fake.text(max_nb_chars=150)}",
                                }
                                if created_data.get("job") is None:
                                    created_data.update(
                                        {"special_assignment": random_special_assignment}
                                    )
                                    del created_data["job"]
                                debugging_print(created_data)
                            case _:
                                self.stdout_output(
                                    "error", f"Model - {current_model} not exists!"
                                )
                                break

        except Exception as ex:
            self.stdout_output("error", str(ex))
