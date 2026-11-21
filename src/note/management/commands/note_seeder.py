import random
import textwrap
import traceback

from django.db import transaction

from client.models import ClientProxy
from core.choices import NoteSectionEnum
from core.management.mixins.base_seeder_command import BaseSeederCommandMixin
from core.utils.developments.debugging_print_object import DebuggingPrint
from core.utils.developments.debugging_print_types import DPOTableOptions
from job.models import JobProxy
from note.models import Note
from task.models import TaskProxy


class Command(BaseSeederCommandMixin):

    def handle(self, *args, **options):
        try:
            number = options.get("number")
            p_table_jobs_rows = []
            table_header_cols = ["ID", "Title", "Body", "Section", "Client", "Job", "Task"]
            with transaction.atomic():
                for i in range(int(number)):
                    random_section = random.choice(NoteSectionEnum.choices)[0]
                    note_data = {
                        "title": self.FAKER_OBJ.text(max_nb_chars=60),
                        "body": self.FAKER_OBJ.paragraph(),
                    }
                    if random_section == NoteSectionEnum.CLIENT:
                        random_client = random.choice(ClientProxy.objects.all())
                        note_data.update(
                            {
                                "client": random_client,
                            }
                        )
                    elif random_section == NoteSectionEnum.JOB:
                        random_job = random.choice(JobProxy.objects.all())
                        note_data.update(
                            {
                                "job": random_job,
                            }
                        )
                    elif random_section == NoteSectionEnum.TASK:
                        random_task = random.choice(TaskProxy.objects.all())
                        note_data.update(
                            {
                                "task": random_task,
                            }
                        )
                    # DebuggingPrint.pprint(note_data)
                    note_obj = Note.objects.create(**note_data)
                    p_table_jobs_rows.append(
                        [
                            str(note_obj.pk),
                            note_obj.title,
                            textwrap.shorten(note_obj.body, width=30, placeholder="..."),
                            note_obj.note_section,
                            str(note_obj.client.pk if note_obj.client else "---"),
                            str(note_obj.job.pk if note_obj.job else "---"),
                            str(note_obj.task.pk if note_obj.task else "---"),
                        ]
                    )
                table_options: DPOTableOptions = {
                    "show_header": True,
                    "highlight": True,
                    "show_lines": True,
                    "title": "Notes",
                }
                table_obj = DebuggingPrint.table(
                    columns_headers=table_header_cols,
                    rows=p_table_jobs_rows,
                    table_options=table_options,
                )
                # DebuggingPrint.pprint(table_obj)

        except Exception:
            self.stdout_output("error", traceback.format_exc())
