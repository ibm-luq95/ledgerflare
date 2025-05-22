# -*- coding: utf-8 -*-#
import traceback
from pathlib import PosixPath
from datetime import datetime, date
import json
import decouple
from django.core.management import BaseCommand
from django.db import transaction
from django.utils.translation import gettext as _
from import_export.resources import ModelResource

from core.management.mixins import CommandStdOutputMixin
from core.utils.developments.debugging_print_object import DebuggingPrint
from core.utils.developments.debugging_prompt import DebuggingPrompt
from core.utils.grab_env_file import grab_env_file


class ExportingCommandMixin(BaseCommand, CommandStdOutputMixin):
    help = _("Export base command")

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.resources_object: ModelResource | None = None
        self.file_name: str | None = None
        self.app_name: str | None = None
        self.help_message: str | None = None
        self.help = self.help_message

    def add_arguments(self, parser):
        try:
            today_date = date.today()
            config = grab_env_file()
            exported_folder = config("EXPORTED_FROM_CLI_DIR", cast=str)
            self.exported_folder_path: PosixPath = PosixPath(exported_folder)
            if not self.exported_folder_path.exists():
                DebuggingPrint.print("[red bold] Export directory not exists!")
                return
            self.exported_folder_path: PosixPath = PosixPath(exported_folder) / PosixPath(
                str(today_date)
            )
            if self.exported_folder_path.exists() is False:
                DebuggingPrint.print(
                    f"[yellow bold] Today's date ({today_date}) directory not exists, creating..."
                )
                self.exported_folder_path.mkdir(parents=True)
            file_name = f"{self.file_name}_{today_date}"
            parser.add_argument(
                "--export-path",
                "-p",
                type=str,
                default=exported_folder,
                help=_("Exported Path"),
                required=False,
            )
            parser.add_argument(
                "--file-name",
                "-n",
                type=str,
                default=file_name,
                help=_("Exported file name"),
                required=False,
            )
            parser.add_argument(
                "--format",
                "-f",
                type=str,
                default="csv",
                choices=["csv", "json", "html"],
                help=_("File format"),
                required=False,
            )
        except decouple.decouple.UndefinedValueError:
            DebuggingPrint.print("[red bold] Export directory not exists!")
            return
        except Exception as e:
            DebuggingPrint.print(e)
            traceback.print_exc()
            return

    def handle(self, *args, **options):
        try:
            export_path = options.get("export_path")
            name = options.get("file_name")
            format = options.get("format")
            name = f"{name}.{format}"
            full_path: PosixPath = self.exported_folder_path / PosixPath(name)
            # DebuggingPrint.pprint(locals())

            resource = self.resources_object
            queryset = resource._meta.model.original_objects.all()
            # DebuggingPrint.log(queryset)
            # DebuggingPrint.log(len(queryset))
            # DebuggingPrint.rule(text="ddddddddd")
            # queryset = resource._meta.model.objects.all()
            # DebuggingPrint.log(len(queryset))
            # return

            with transaction.atomic():
                # cnfm = DebuggingPrompt.confirm(
                #     _(f"Are you sure want to start exporting {self.app_name}s?")
                # )

                # if cnfm is True:
                total_rows = len(queryset)
                dataset = resource.export(queryset)
                DebuggingPrint.pprint(f"Total rows {total_rows}")
                # DebuggingPrint.inspect(dataset, is_all=True)
                with open(full_path, "wb") as fp:
                    if format == "csv":
                        fp.write(dataset.csv.encode("utf-8"))
                    elif format == "json":
                        data = dataset.json.encode("utf-8")
                        load_data = json.loads(data)
                        dump = json.dumps(load_data, indent=4)
                        fp.write(data)
                    elif format == "html":
                        fp.write(dataset.html.encode("utf-8"))
                    else:
                        self.stdout_output("error", _("Format not valid"))
                # else:
                #     return

        except Exception as ex:
            self.stdout_output("error", traceback.format_exc())
            return
