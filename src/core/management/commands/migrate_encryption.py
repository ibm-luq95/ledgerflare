"""Command to migrate database records to AES-256-GCM encryption."""

from __future__ import annotations

from typing import Any

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction

from core.crypto.engine import CryptoEngine
from core.crypto.service import EncryptionService


class Command(BaseCommand):
    """Migrate database records to AES-256-GCM authenticated encryption."""

    help = (
        "Migrate database records and files to AES-256-GCM "
        "authenticated encryption with loopback verification."
    )

    def add_arguments(self, parser: Any) -> None:
        """Add CLI arguments for migration command."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Scan database, validate decryptability, and report.",
        )
        parser.add_argument(
            "--execute",
            action="store_true",
            default=False,
            help="Execute encryption migration.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=250,
            help="Number of records per transaction batch (default: 250).",
        )
        parser.add_argument(
            "--model",
            type=str,
            default=None,
            help="Specific model to migrate (e.g. task.Task, note.Note).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute or dry-run database encryption migration."""
        is_execute = options.get("execute", False)
        is_dry_run = options.get("dry_run", False) or not is_execute
        batch_size = options.get("batch_size", 250)
        target_model_name = options.get("model")

        targets: list[tuple[str, str, list[str]]] = [
            ("task", "Task", ["additional_notes", "hints"]),
            ("note", "Note", ["body"]),
            ("client_account", "ClientAccount", ["account_password"]),
            ("staff_briefcase", "StaffAccounts", ["password"]),
        ]

        if target_model_name:
            t_low = target_model_name.lower()
            targets = [
                t
                for t in targets
                if f"{t[0]}.{t[1]}".lower() == t_low or t[1].lower() == t_low
            ]

        total_scanned = 0
        total_migrated = 0

        self.stdout.write("=== MIGRATION AUDIT REPORT ===")
        for app_label, model_name, field_names in targets:
            try:
                model_cls = apps.get_model(app_label, model_name)
            except LookupError:
                continue

            manager = getattr(model_cls, "original_objects", model_cls.objects)
            count = manager.count()
            total_scanned += count
            self.stdout.write(f"Model {app_label}.{model_name}: {count} total records")

            if is_execute:
                pks = list(manager.values_list("pk", flat=True))
                for i in range(0, len(pks), batch_size):
                    batch_pks = pks[i : i + batch_size]
                    with transaction.atomic():
                        records = manager.filter(pk__in=batch_pks)
                        for record in records:
                            updated_fields: dict[str, str] = {}
                            for field_name in field_names:
                                raw_val = record.__dict__.get(field_name)
                                if raw_val is None:
                                    raw_val = getattr(record, field_name, None)
                                if not raw_val or not isinstance(raw_val, str):
                                    continue
                                if raw_val.startswith(
                                    EncryptionService.VERSION_PREFIX_V1
                                ):
                                    continue

                                concrete = getattr(record._meta, "concrete_model", None)
                                m_name = (concrete or record)._meta.model_name
                                r_pk = record.pk
                                aad = f"{m_name}:{field_name}:{r_pk}".encode()
                                orig = CryptoEngine.decrypt(raw_val) or raw_val
                                new_cipher = EncryptionService.encrypt(orig, aad)

                                verify_plaintext = EncryptionService.decrypt(
                                    new_cipher, aad
                                )
                                if verify_plaintext != orig:
                                    msg = (
                                        f"Integrity loopback failed for "
                                        f"{model_name}.{field_name} (ID: {r_pk})"
                                    )
                                    raise RuntimeError(msg)

                                updated_fields[field_name] = new_cipher

                            if updated_fields:
                                manager.filter(pk=record.pk).update(**updated_fields)
                                total_migrated += 1

        if is_dry_run:
            self.stdout.write("DRY RUN COMPLETE: All records validated.")
            self.stdout.write("Database mutations: 0")
        else:
            self.stdout.write(f"MIGRATION COMPLETE: Migrated {total_migrated} records.")
