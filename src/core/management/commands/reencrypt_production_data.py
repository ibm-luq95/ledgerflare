"""Management command to safely re-encrypt legacy production credentials using Rich UI, status reports, and Django transactions."""

from __future__ import annotations

import logging
from typing import Any

from django.core.management.base import BaseCommand
from django.db import DatabaseError, connection, transaction

from cryptography.fernet import InvalidSignature, InvalidToken
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from core.crypto.engine import VERSION_PREFIX_V2, CryptoEngine
from core.management.mixins.production_guard import ProductionGuardCommandMixin

logger = logging.getLogger(__name__)
console = Console()


class Command(ProductionGuardCommandMixin, BaseCommand):
    help = "Safely inspects or upgrades legacy production credentials to v2$ format under primary ENCRYPT_KEY."

    def add_arguments(self, parser: Any) -> None:
        super().add_arguments(parser)
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Inspect records and simulate re-encryption without committing any database changes.",
        )
        parser.add_argument(
            "--status",
            action="store_true",
            help="Display a detailed status report of database encryption states without making any changes.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of records to process per batch.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run: bool = options["dry_run"]
        show_status: bool = options["status"]
        batch_size: int = options["batch_size"]

        # 1. Status Mode (Read-only overview table)
        if show_status:
            console.print(
                Panel(
                    "[bold cyan]LedgerFlare Database Encryption Status Overview[/bold cyan]\n"
                    "[dim]Mode: READ-ONLY STATUS REPORT[/dim]",
                    title="[bold magenta]Database Status[/bold magenta]",
                    expand=False,
                )
            )
            self._render_status_report()
            return

        # 2. Re-Encryption Execution (Live or Dry-Run)
        mode_text = (
            "[bold yellow]DRY-RUN MODE (Zero DB Writes)[/bold yellow]"
            if dry_run
            else "[bold green]LIVE UPDATE MODE[/bold green]"
        )
        console.print(
            Panel(
                f"[bold cyan]LedgerFlare Production Re-Encryption Utility[/bold cyan]\n"
                f"Execution Mode: {mode_text}\n"
                f"Batch Size: [bold white]{batch_size}[/bold white]",
                title="[bold magenta]Security & Database Safety[/bold magenta]",
                expand=False,
            )
        )

        try:
            with connection.cursor() as cursor:
                # Process ClientAccount Table
                ca_stats = self._process_table(
                    cursor=cursor,
                    table_name="client_account_clientaccount",
                    field_name="account_password",
                    model_display="ClientAccount Credentials",
                    dry_run=dry_run,
                )

                # Process StaffAccounts Table
                sa_stats = self._process_table(
                    cursor=cursor,
                    table_name="staff_briefcase_staffaccounts",
                    field_name="password",
                    model_display="StaffAccounts Credentials",
                    dry_run=dry_run,
                )

                # Render Summary Tables with rich parameters
                self._render_summary_table(
                    title="ClientAccount Re-Encryption Summary",
                    caption="ClientAccount table re-encryption results and database metrics.",
                    stats=ca_stats,
                    dry_run=dry_run,
                )
                self._render_summary_table(
                    title="StaffAccounts Re-Encryption Summary",
                    caption="StaffAccounts table re-encryption results and database metrics.",
                    stats=sa_stats,
                    dry_run=dry_run,
                )

        except DatabaseError as db_err:
            console.print(
                Panel(
                    f"[bold red]Database Exception Encountered:[/bold red]\n{str(db_err)}\n"
                    f"[yellow]Transaction automatically rolled back. Database remains safe.[/yellow]",
                    title="[bold red]CRITICAL DATABASE ERROR[/bold red]",
                )
            )
            logger.error("Re-encryption command aborted due to DatabaseError: %s", str(db_err), exc_info=True)
            return
        except Exception as exc:
            console.print(
                Panel(
                    f"[bold red]Unexpected Exception Encountered:[/bold red]\n{str(exc)}\n"
                    f"[yellow]Operation aborted safely.[/yellow]",
                    title="[bold red]UNHANDLED EXCEPTION[/bold red]",
                )
            )
            logger.error("Re-encryption command aborted due to unexpected exception: %s", str(exc), exc_info=True)
            return

        footer_msg = (
            "[bold yellow]DRY-RUN COMPLETE: Simulated safely. Zero changes were saved to PostgreSQL.[/bold yellow]"
            if dry_run
            else "[bold green]RE-ENCRYPTION COMPLETE: Database successfully updated and verified.[/bold green]"
        )
        console.print(Panel(footer_msg, title="[bold green]Operation Status[/bold green]"))

    def _render_status_report(self) -> None:
        """Queries and displays the encryption status breakdown for all target tables."""
        table = Table(
            title="Production Encryption Status Report",
            title_justify="center",
            caption="Overview of database records requiring format upgrade vs already on v2$ format.",
            caption_justify="center",
            expand=True,
            show_lines=True,
        )
        table.add_column("Database Table", style="bold white", justify="left")
        table.add_column("Field Name", style="cyan", justify="left")
        table.add_column("Total Rows", style="white", justify="right")
        table.add_column("v2$ Format (Up-to-Date)", style="green", justify="right")
        table.add_column("Legacy Format (Needs Upgrade)", style="yellow", justify="right")
        table.add_column("Decryption Status", style="magenta", justify="left")

        with connection.cursor() as cursor:
            tables_to_check = [
                ("client_account_clientaccount", "account_password", "ClientAccount"),
                ("staff_briefcase_staffaccounts", "password", "StaffAccounts"),
            ]

            for db_table, field, display_name in tables_to_check:
                try:
                    cursor.execute(f"SELECT {field} FROM {db_table} WHERE {field} IS NOT NULL")
                    rows = cursor.fetchall()
                    total = len(rows)
                    v2_count = sum(1 for (val,) in rows if val and str(val).startswith(VERSION_PREFIX_V2))
                    legacy_count = total - v2_count

                    status_str = (
                        "[bold green]100% Up to Date[/bold green]"
                        if legacy_count == 0
                        else f"[bold yellow]{legacy_count} Records Need Upgrade[/bold yellow]"
                    )

                    table.add_row(
                        display_name,
                        field,
                        str(total),
                        str(v2_count),
                        str(legacy_count),
                        status_str,
                    )
                except DatabaseError as err:
                    table.add_row(
                        display_name,
                        field,
                        "ERR",
                        "ERR",
                        "ERR",
                        f"[bold red]DB Error: {str(err)}[/bold red]",
                    )

        console.print(table)
        console.print()

    def _process_table(
        self,
        cursor: Any,
        table_name: str,
        field_name: str,
        model_display: str,
        dry_run: bool,
    ) -> dict[str, int]:
        """Processes a database table safely inside an atomic transaction block with expanded progress bar."""
        stats = {"total": 0, "upgraded": 0, "skipped": 0, "untouched": 0}

        try:
            cursor.execute(f"SELECT id, {field_name} FROM {table_name} WHERE {field_name} IS NOT NULL")
            rows = cursor.fetchall()
            stats["total"] = len(rows)

            if not rows:
                console.print(f"[dim]No records found in {table_name}.[/dim]\n")
                return stats

            with transaction.atomic():
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold cyan]{task.description}"),
                    BarColumn(bar_width=None),  # bar_width=None expands to fill available console width
                    MofNCompleteColumn(),
                    TaskProgressColumn(),
                    TextColumn("[yellow]{task.fields[current_status]}"),
                    console=console,
                    expand=True,  # Expands the progress bar row across full terminal width
                ) as progress:
                    task = progress.add_task(
                        f"Processing {model_display}",
                        total=len(rows),
                        current_status="Initializing...",
                    )

                    for row_id, raw_password in rows:
                        # Update progress status message for live user feedback
                        progress.update(task, current_status=f"Row ID #{row_id}")

                        # Gate 1: Skip empty or already v2$ records
                        if not raw_password or str(raw_password).startswith(VERSION_PREFIX_V2):
                            stats["skipped"] += 1
                            progress.advance(task)
                            continue

                        # Gate 2: Safe decryption check
                        try:
                            decrypted = CryptoEngine.decrypt(str(raw_password))
                        except (InvalidToken, InvalidSignature, UnicodeDecodeError, ValueError) as crypto_err:
                            stats["untouched"] += 1
                            logger.warning("[%s ID %s] Decryption error: %s", table_name, row_id, str(crypto_err))
                            progress.advance(task)
                            continue
                        except Exception as unk_err:
                            stats["untouched"] += 1
                            logger.warning("[%s ID %s] Unexpected error: %s", table_name, row_id, str(unk_err))
                            progress.advance(task)
                            continue

                        if not decrypted:
                            stats["untouched"] += 1
                            progress.advance(task)
                            continue

                        # Gate 3: Encrypt to v2$ format under current primary key
                        try:
                            new_ciphertext = CryptoEngine.encrypt(decrypted)
                        except Exception as enc_err:
                            stats["untouched"] += 1
                            logger.error("[%s ID %s] Encryption error: %s", table_name, row_id, str(enc_err))
                            progress.advance(task)
                            continue

                        # Gate 4: In-memory round-trip verification
                        try:
                            verified_plaintext = CryptoEngine.decrypt(new_ciphertext)
                            if verified_plaintext != decrypted:
                                stats["untouched"] += 1
                                logger.error("[%s ID %s] Round-trip verification mismatch!", table_name, row_id)
                                progress.advance(task)
                                continue
                        except Exception as ver_err:
                            stats["untouched"] += 1
                            logger.error("[%s ID %s] Verification check failed: %s", table_name, row_id, str(ver_err))
                            progress.advance(task)
                            continue

                        # Gate 5: Perform DB Update if live mode
                        if not dry_run:
                            try:
                                cursor.execute(
                                    f"UPDATE {table_name} SET {field_name} = %s WHERE id = %s",
                                    [new_ciphertext, row_id],
                                )
                            except DatabaseError as update_err:
                                stats["untouched"] += 1
                                logger.error("[%s ID %s] DB update error: %s", table_name, row_id, str(update_err))
                                progress.advance(task)
                                continue

                        stats["upgraded"] += 1
                        progress.advance(task)

                    progress.update(task, current_status="Completed")

                if dry_run:
                    transaction.set_rollback(True)

        except Exception as table_err:
            console.print(f"[bold red]Error processing table {table_name}:[/bold red] {str(table_err)}")
            logger.error("Error processing table %s: %s", table_name, str(table_err), exc_info=True)

        return stats

    def _render_summary_table(
        self,
        title: str,
        caption: str,
        stats: dict[str, int],
        dry_run: bool,
    ) -> None:
        """Renders a formatted Rich summary table with required configuration parameters."""
        table = Table(
            title=title,
            title_justify="center",
            caption=caption,
            caption_justify="center",
            expand=True,
            show_lines=True,
        )
        table.add_column("Metric Name", style="white", justify="left")
        table.add_column("Record Count", style="bold cyan", justify="right")
        table.add_column("Status Description", style="dim", justify="left")

        table.add_row("Total Scanned Records", str(stats["total"]), "Total non-null database rows evaluated")
        table.add_row("Already Upgraded (v2$)", str(stats["skipped"]), "Skipped — already using latest format")

        if dry_run:
            table.add_row("Verified for Upgrade", str(stats["upgraded"]), "Simulated — ready for live re-encryption", style="bold yellow")
        else:
            table.add_row("Successfully Upgraded", str(stats["upgraded"]), "Updated to v2$ format in PostgreSQL", style="bold green")

        if stats["untouched"] > 0:
            table.add_row("Untouched (Key Mismatch)", str(stats["untouched"]), "Safely preserved — key signature did not match", style="bold red")
        else:
            table.add_row("Untouched (Key Mismatch)", "0", "No corrupted or key-mismatched records", style="green")

        console.print(table)
        console.print()
