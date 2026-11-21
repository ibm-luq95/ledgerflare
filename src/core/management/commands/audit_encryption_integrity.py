"""Management command to audit encryption integrity."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from rich.console import Console
from rich.table import Table

from core.crypto.container import MAGIC as MAGIC_V2
from core.crypto.service import EncryptionService


console = Console()


class Command(BaseCommand):
    """Audit cryptographic integrity of all database records and on-disk files."""

    help = (
        "Verify 100% encryption coverage and decryptability across all "
        "sensitive database models and confidential file attachments."
    )

    def add_arguments(self, parser: Any) -> None:
        """Add CLI arguments for audit command."""
        parser.add_argument(
            "--full",
            action="store_true",
            default=False,
            help="Perform full decryptability verification on all ciphertexts.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute cryptographic integrity audit."""
        is_full = bool(options.get("full", False))

        console.print(
            "\n[bold cyan]=== LEDGERFLARE CRYPTOGRAPHIC AUDIT ===[/bold cyan]\n"
        )

        db_targets: list[tuple[str, str, list[str]]] = [
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

        file_targets: list[tuple[str, str, str]] = [
            ("document", "Document", "document_file"),
            ("staff_briefcase", "StaffDocuments", "document_file"),
            ("special_assignment", "SpecialAssignment", "attachment"),
            ("discussion", "Discussion", "attachment"),
        ]

        total_violations = 0

        # 1. Audit Database Records
        db_table = Table(title="Database Models Encryption Audit", show_header=True)
        db_table.add_column("Model", style="bold cyan")
        db_table.add_column("Fields", style="cyan")
        db_table.add_column("Total Rows", justify="right")
        db_table.add_column("Encrypted (v1:)", justify="right", style="green")
        db_table.add_column("Unencrypted Violations", justify="right", style="bold red")

        for app_label, model_name, field_names in db_targets:
            try:
                model_cls = apps.get_model(app_label, model_name)
            except LookupError:
                continue

            manager = getattr(model_cls, "original_objects", model_cls.objects)
            count = manager.count()

            m_encrypted = 0
            m_violations = 0

            records = list(manager.values("pk", *field_names))
            concrete = getattr(model_cls._meta, "concrete_model", model_cls)
            m_canonical_name = concrete._meta.model_name

            for rec in records:
                rec_pk = str(rec["pk"])
                for field_name in field_names:
                    val = rec.get(field_name)
                    if not val or not isinstance(val, str):
                        continue

                    if not val.startswith(EncryptionService.VERSION_PREFIX_V1):
                        m_violations += 1
                        total_violations += 1
                    else:
                        m_encrypted += 1
                        if is_full:
                            aad = f"{m_canonical_name}:{field_name}:{rec_pk}".encode()
                            try:
                                EncryptionService.decrypt(val, aad)
                            except Exception:  # noqa: BLE001
                                m_violations += 1
                                total_violations += 1

            status_style = "green" if m_violations == 0 else "bold red"
            db_table.add_row(
                f"{app_label}.{model_name}",
                ", ".join(field_names),
                str(count),
                str(m_encrypted),
                f"[{status_style}]{m_violations}[/{status_style}]",
            )

        console.print(db_table)

        # 2. Audit File Attachments
        file_table = Table(title="File Storage Encryption Audit", show_header=True)
        file_table.add_column("Model", style="bold cyan")
        file_table.add_column("Field", style="cyan")
        file_table.add_column("Total Files", justify="right")
        file_table.add_column("LFENC02 Containers", justify="right", style="green")
        file_table.add_column(
            "Unencrypted Violations", justify="right", style="bold red"
        )
        file_table.add_column("Quarantined (Missing)", justify="right", style="yellow")

        for app_label, model_name, field_name in file_targets:
            try:
                model_cls = apps.get_model(app_label, model_name)
            except LookupError:
                continue

            manager = getattr(model_cls, "original_objects", model_cls.objects)
            qs = manager.filter(**{f"{field_name}__isnull": False}).exclude(**{
                field_name: ""
            })
            count = qs.count()

            f_encrypted = 0
            f_violations = 0
            f_quarantined = 0

            for rec in qs:
                file_field = getattr(rec, field_name, None)
                if not file_field or not getattr(file_field, "name", None):
                    continue

                try:
                    f_path = Path(file_field.path)
                except ValueError, NotImplementedError:
                    f_quarantined += 1
                    continue

                if not f_path.exists():
                    f_quarantined += 1
                    continue

                try:
                    with f_path.open("rb") as f:
                        header = f.read(8)

                    if header == MAGIC_V2:
                        f_encrypted += 1
                    else:
                        f_violations += 1
                        total_violations += 1
                except Exception:  # noqa: BLE001
                    f_violations += 1
                    total_violations += 1

            status_style = "green" if f_violations == 0 else "bold red"
            file_table.add_row(
                f"{app_label}.{model_name}",
                field_name,
                str(count),
                str(f_encrypted),
                f"[{status_style}]{f_violations}[/{status_style}]",
                str(f_quarantined),
            )

        console.print(file_table)

        if total_violations > 0:
            console.print(
                f"\n[bold red]AUDIT FAILED: {total_violations} violations.[/bold red]"
            )
            msg = f"Cryptographic audit failed with {total_violations} violations."
            raise CommandError(msg)

        console.print(
            "\n[bold green]AUDIT PASSED: 100% compliance. 0 violations.[/bold green]\n"
        )
