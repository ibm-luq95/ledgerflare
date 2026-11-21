"""Management command to migrate database records to AES-256-GCM encryption."""

from __future__ import annotations

from typing import Any

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from rich.console import Console

from core.crypto.blind_index import compute_trigram_blind_index
from core.crypto.engine import CryptoEngine
from core.crypto.reporter import MigrationReporter
from core.crypto.service import EncryptionService


console = Console()


class Command(BaseCommand):
    """Safely migrate database records to AES-256-GCM authenticated encryption."""

    help = (
        "Migrate database records to AES-256-GCM authenticated encryption "
        "with AAD binding, trigram blind indexing, rollback, and reporting."
    )

    def add_arguments(self, parser: Any) -> None:
        """Add CLI arguments for database migration command."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Scan database without saving (default).",
        )
        parser.add_argument(
            "--execute",
            action="store_true",
            default=False,
            help="Execute the database encryption migration.",
        )
        parser.add_argument(
            "--reverse",
            action="store_true",
            default=False,
            help="Revert encrypted database fields back to plain text.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=250,
            help="Number of records per transaction batch (default: 250).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum number of records to process per model.",
        )
        parser.add_argument(
            "--model",
            type=str,
            default=None,
            help="Specific model to migrate (e.g. client_account.ClientAccount).",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default=None,
            help="Custom directory to store persistent reports and manifest.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute or dry-run database encryption migration."""
        is_execute = bool(options.get("execute", False))
        is_reverse = bool(options.get("reverse", False))
        is_dry_run = bool(options.get("dry_run", False)) or not is_execute
        batch_size = int(options.get("batch_size") or 250)
        limit = options.get("limit")
        target_model_name = options.get("model")
        output_dir = options.get("output_dir")

        mode_name = (
            "reverse" if is_reverse else ("execute" if is_execute else "dry_run")
        )
        reporter = MigrationReporter(
            command_name="migrate_db_encryption", mode=mode_name
        )

        # Pre-flight cryptographic self-test
        try:
            EncryptionService._get_key_bytes()
        except Exception as ex:
            msg = f"Cryptographic pre-flight check failed: {ex}"
            raise CommandError(msg) from ex

        targets: list[tuple[str, str, list[str]]] = [
            (
                "client_account",
                "ClientAccount",
                ["account_username", "account_url", "account_password"],
            ),
            (
                "staff_briefcase",
                "StaffAccounts",
                ["username_email", "url", "password"],
            ),
            ("staff_briefcase", "StaffNotes", ["note"]),
            ("special_assignment", "SpecialAssignment", ["body", "notes"]),
            ("discussion", "Discussion", ["body"]),
            ("important_contact", "ImportantContact", ["contact_notes"]),
            ("job", "Job", ["note"]),
            ("note", "Note", ["body"]),
            ("task", "Task", ["hints", "additional_notes"]),
        ]

        if target_model_name:
            t_low = target_model_name.lower()
            targets = [
                t
                for t in targets
                if f"{t[0]}.{t[1]}".lower() == t_low or t[1].lower() == t_low
            ]

        console.print(
            "\n[bold cyan]=== DATABASE RECORD ENCRYPTION MIGRATION ===[/bold cyan]"
        )
        mode_str = (
            "[bold red]REVERSE ROLLBACK (Decrypting to plaintext)[/bold red]"
            if is_reverse
            else (
                "[bold green]EXECUTE (Encrypting database records)[/bold green]"
                if is_execute
                else "[bold yellow]DRY-RUN (No database modifications)[/bold yellow]"
            )
        )
        console.print(f"Operational Mode: {mode_str}\n")

        for app_label, model_name, field_names in targets:
            try:
                model_cls = apps.get_model(app_label, model_name)
            except LookupError:
                continue

            manager = getattr(model_cls, "original_objects", model_cls.objects)
            qs = manager.all()
            if limit:
                qs = qs[:limit]

            count = qs.count()
            m_skipped = 0
            m_migrated = 0
            m_conflicts = 0
            m_errors = 0

            # Canonical model identifier for AAD binding
            concrete = getattr(model_cls._meta, "concrete_model", None)
            m_canonical_name = (concrete or model_cls)._meta.model_name

            records = list(qs.iterator(chunk_size=batch_size))
            for record in records:
                record_pk = str(record.pk)
                updated_fields: dict[str, Any] = {}
                needs_update = False

                for field_name in field_names:
                    raw_val = record.__dict__.get(field_name)
                    if raw_val is None:
                        raw_val = getattr(record, field_name, None)

                    if not raw_val or not isinstance(raw_val, str):
                        continue

                    aad = f"{m_canonical_name}:{field_name}:{record_pk}".encode()
                    is_encrypted = raw_val.startswith(
                        EncryptionService.VERSION_PREFIX_V1
                    )

                    if is_reverse:
                        if not is_encrypted:
                            continue
                        needs_update = True
                        decrypted_text = EncryptionService.decrypt(raw_val, aad)
                        updated_fields[field_name] = decrypted_text

                        # Clear companion trigram blind index
                        bidx_field_name = f"{field_name}_bidx"
                        if hasattr(record, bidx_field_name):
                            updated_fields[bidx_field_name] = []
                    else:
                        if is_encrypted:
                            continue

                        needs_update = True
                        # Decrypt legacy if needed, or take raw plaintext
                        if raw_val.startswith(("v2$", "gAAAAA")):
                            orig_text = CryptoEngine.decrypt(raw_val) or raw_val
                        else:
                            orig_text = raw_val

                        # Encrypt with AES-256-GCM and bound AAD
                        new_cipher = EncryptionService.encrypt(orig_text, aad)

                        # Loopback verification
                        verified_text = EncryptionService.decrypt(new_cipher, aad)
                        if verified_text != orig_text:
                            msg = f"Loopback failed on {model_name}.{field_name}"
                            raise RuntimeError(msg)

                        updated_fields[field_name] = new_cipher

                        # Populate trigram blind index if model has _bidx field
                        bidx_field_name = f"{field_name}_bidx"
                        if hasattr(record, bidx_field_name):
                            context = f"{m_canonical_name}:{field_name}"
                            tokens = compute_trigram_blind_index(
                                orig_text, context=context
                            )
                            updated_fields[bidx_field_name] = tokens

                if not needs_update:
                    m_skipped += 1
                    continue

                if is_dry_run:
                    m_migrated += 1
                    continue

                # Execute with optimistic concurrency: verify updated_at
                try:
                    with transaction.atomic():
                        filter_kwargs = {"pk": record.pk}
                        if hasattr(record, "updated_at") and record.updated_at:
                            filter_kwargs["updated_at"] = record.updated_at

                        rows_updated = manager.filter(**filter_kwargs).update(
                            **updated_fields
                        )
                        if rows_updated == 0:
                            m_conflicts += 1
                            reporter.record_quarantine(
                                model=f"{app_label}.{model_name}",
                                pk=str(record.pk),
                                field=", ".join(field_names),
                                path="database",
                                issue_type="CONCURRENCY_CONFLICT",
                                error=(
                                    "Record was updated concurrently during migration"
                                ),
                            )
                        else:
                            m_migrated += 1

                except Exception as ex:
                    console.print(
                        f"[bold red]Error updating {model_name} "
                        f"{record.pk}: {ex}[/bold red]"
                    )
                    m_errors += 1
                    reporter.record_quarantine(
                        model=f"{app_label}.{model_name}",
                        pk=str(record.pk),
                        field=", ".join(field_names),
                        path="database",
                        issue_type="ERROR",
                        error=str(ex),
                    )
                    raise

            reporter.record_target(
                target_name=f"{app_label}.{model_name} ({', '.join(field_names)})",
                total_count=count,
                migrated=m_migrated,
                skipped=m_skipped,
                quarantined=0,
                conflicts=m_conflicts,
                errors=m_errors,
            )

        json_path, md_path = reporter.write_reports(output_dir=output_dir)
        reporter.print_summary(console=console)
        console.print(f"\n[bold cyan]Report saved to:[/bold cyan] {json_path}")
        console.print(f"[bold cyan]Markdown summary:[/bold cyan] {md_path}\n")
