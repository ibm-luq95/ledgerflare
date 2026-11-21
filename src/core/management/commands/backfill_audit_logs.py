from __future__ import annotations

import json
from typing import Any
from dateutil import parser

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = "Safely backfills historical CRUD logs from django-easy-audit to django-auditlog"

    def handle(self, *args: Any, **options: Any) -> None:
        LogEntry = apps.get_model("auditlog", "LogEntry")
        
        chunk_size = 2000
        last_id = 0
        migrated_count = 0

        self.stdout.write(self.style.NOTICE("Starting database backfill..."))

        # Verify table exists in the database
        with connection.cursor() as cursor:
            tables = connection.introspection.table_names()
            if "easyaudit_crudevent" not in tables:
                self.stdout.write(self.style.ERROR("easyaudit_crudevent table does not exist in the database!"))
                return

        while True:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT id, event_type, object_id, content_type_id, object_repr, "
                    f"object_json_repr, changed_fields, user_id, datetime, user_pk_as_string "
                    f"FROM easyaudit_crudevent WHERE id > {int(last_id)} ORDER BY id LIMIT {int(chunk_size)}"
                )
                rows = cursor.fetchall()

            if not rows:
                break

            entries_to_create = []
            for row in rows:
                row_id = row[0]
                event_type = row[1]
                object_id_str = row[2]
                content_type_id = row[3]
                object_repr = row[4]
                object_json_repr = row[5]
                changed_fields = row[6]
                user_id = row[7]
                event_datetime = row[8]
                user_pk_as_string = row[9]

                last_id = row_id

                if event_type == 1:
                    action = 0
                elif event_type == 3:
                    action = 2
                else:
                    action = 1

                changes_dict = {}
                if changed_fields:
                    try:
                        parsed = json.loads(changed_fields)
                        if isinstance(parsed, dict):
                            changes_dict = parsed
                            if event_type in [4, 5, 6, 7, 8, 9, 10, 11]:
                                operation = "add" if event_type in [6, 7] else ("delete" if event_type in [8, 9] else "clear")
                                for rel_field, pks in list(changes_dict.items()):
                                    if isinstance(pks, list):
                                        changes_dict[rel_field] = {
                                            "type": "m2m",
                                            "operation": operation,
                                            "objects": [str(pk) for pk in pks]
                                        }
                        elif isinstance(parsed, list):
                            changes_dict = {"m2m_clear": parsed}
                    except json.JSONDecodeError:
                        pass

                serialized_data = None
                if object_json_repr:
                    try:
                        serialized_data = json.loads(object_json_repr)
                    except json.JSONDecodeError:
                        pass

                try:
                    numeric_object_id = int(object_id_str)
                except (ValueError, TypeError):
                    numeric_object_id = None

                timestamp = event_datetime
                if isinstance(timestamp, str):
                    timestamp = parser.parse(timestamp)

                entry = LogEntry(
                    content_type_id=content_type_id,
                    object_pk=object_id_str,
                    object_id=numeric_object_id,
                    object_repr=object_repr or "",
                    action=action,
                    changes=changes_dict,
                    serialized_data=serialized_data,
                    actor_id=user_id,
                    timestamp=timestamp,
                    additional_data={
                        "legacy_user_pk_as_string": user_pk_as_string,
                        "migrated_from": "django-easy-audit"
                    }
                )
                entries_to_create.append(entry)

            with transaction.atomic():
                LogEntry.objects.bulk_create(entries_to_create)

            migrated_count += len(entries_to_create)
            self.stdout.write(self.style.SUCCESS(f"Migrated {migrated_count} records. Current legacy ID: {last_id}"))

        self.stdout.write(self.style.SUCCESS(f"Backfill complete! Total migrated records: {migrated_count}"))
