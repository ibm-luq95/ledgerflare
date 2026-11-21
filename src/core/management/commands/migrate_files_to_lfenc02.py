"""Management command to migrate legacy disk files into LFENC02 containers."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from pathlib import Path
from typing import Any

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from rich.console import Console

from core.crypto.container import (
    DEFAULT_CHUNK_SIZE,
    ChunkedContainerEngine,
)
from core.crypto.container import (
    MAGIC as MAGIC_V2,
)
from core.crypto.reporter import MigrationReporter
from core.crypto.service import EncryptionService
from core.crypto.stream import EncryptedStreamReader


console = Console()


class Command(BaseCommand):
    """Safely migrate unencrypted disk files into LFENC02 encrypted containers."""

    help = (
        "Migrate unencrypted disk files to AES-256-GCM chunked LFENC02 containers "
        "with SHA-256 loopback verification, quarantine isolation, and rollback."
    )

    def add_arguments(self, parser: Any) -> None:
        """Add CLI arguments for migration command."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Scan files without modifying disk files (default).",
        )
        parser.add_argument(
            "--execute",
            action="store_true",
            default=False,
            help="Execute the file migration and containerization.",
        )
        parser.add_argument(
            "--reverse",
            action="store_true",
            default=False,
            help="Revert LFENC02 encrypted containers back to plain unencrypted files.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Number of records per batch (default: 50).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum number of files to process per model.",
        )
        parser.add_argument(
            "--model",
            type=str,
            default=None,
            help="Specific model to migrate (e.g. document.Document).",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default=None,
            help="Custom directory to store persistent reports and manifest.",
        )
        parser.add_argument(
            "--min-free-disk-mb",
            type=int,
            default=50,
            help="Minimum free disk space buffer in MB (default: 50).",
        )
        parser.add_argument(
            "--verify-only",
            action="store_true",
            default=False,
            help="Validate decryption of existing LFENC02 files without migrating.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute or dry-run file encryption migration."""
        is_execute = bool(options.get("execute", False))
        is_reverse = bool(options.get("reverse", False))
        is_dry_run = bool(options.get("dry_run", False)) or not is_execute
        limit = options.get("limit")
        target_model_name = options.get("model")
        output_dir = options.get("output_dir")
        min_free_disk_mb = int(options.get("min_free_disk_mb", 50))

        mode_name = (
            "reverse" if is_reverse else ("execute" if is_execute else "dry_run")
        )
        reporter = MigrationReporter(
            command_name="migrate_files_to_lfenc02", mode=mode_name
        )

        # Pre-flight cryptographic self-test
        try:
            EncryptionService._get_key_bytes()
        except Exception as ex:
            msg = f"Cryptographic pre-flight check failed: {ex}"
            raise CommandError(msg) from ex

        targets: list[tuple[str, str, str]] = [
            ("document", "Document", "document_file"),
            ("staff_briefcase", "StaffDocuments", "document_file"),
            ("special_assignment", "SpecialAssignment", "attachment"),
            ("discussion", "Discussion", "attachment"),
        ]

        if target_model_name:
            t_low = target_model_name.lower()
            targets = [
                t
                for t in targets
                if f"{t[0]}.{t[1]}".lower() == t_low or t[1].lower() == t_low
            ]

        console.print(
            "\n[bold cyan]=== LFENC02 FILE STORAGE CONTAINER MIGRATION ===[/bold cyan]"
        )
        mode_str = (
            "[bold red]REVERSE ROLLBACK (Decrypting to plaintext)[/bold red]"
            if is_reverse
            else (
                "[bold green]EXECUTE (Containerizing files)[/bold green]"
                if is_execute
                else "[bold yellow]DRY-RUN (No disk modifications)[/bold yellow]"
            )
        )
        console.print(f"Operational Mode: {mode_str}\n")

        for app_label, model_name, field_name in targets:
            try:
                model_cls = apps.get_model(app_label, model_name)
            except LookupError:
                continue

            manager = getattr(model_cls, "original_objects", model_cls.objects)
            qs = manager.filter(**{f"{field_name}__isnull": False}).exclude(**{
                field_name: ""
            })
            if limit:
                qs = qs[:limit]

            count = qs.count()
            m_skipped = 0
            m_migrated = 0
            m_quarantined = 0
            m_errors = 0

            records = list(qs)
            for record in records:
                file_field = getattr(record, field_name, None)
                if not file_field or not getattr(file_field, "name", None):
                    continue

                try:
                    file_path = Path(file_field.path)
                except (ValueError, NotImplementedError) as ex:
                    m_quarantined += 1
                    reporter.record_quarantine(
                        model=f"{app_label}.{model_name}",
                        pk=str(record.pk),
                        field=field_name,
                        path="unknown",
                        issue_type="INVALID_PATH",
                        error=str(ex),
                    )
                    continue

                if not file_path.exists():
                    m_quarantined += 1
                    reporter.record_quarantine(
                        model=f"{app_label}.{model_name}",
                        pk=str(record.pk),
                        field=field_name,
                        path=str(file_path),
                        issue_type="MISSING_FILE",
                        error=f"FileNotFoundError: {file_path}",
                    )
                    continue

                try:
                    with file_path.open("rb") as f:
                        header_bytes = f.read(8)

                    is_lfenc02 = header_bytes == MAGIC_V2

                    if is_reverse:
                        if not is_lfenc02:
                            m_skipped += 1
                            continue
                        if is_dry_run:
                            m_migrated += 1
                            continue
                        self._revert_file(file_path)
                        m_migrated += 1
                    else:
                        if is_lfenc02:
                            m_skipped += 1
                            continue
                        if is_dry_run:
                            m_migrated += 1
                            continue
                        self._containerize_file(
                            file_path, min_free_disk_mb=min_free_disk_mb
                        )
                        m_migrated += 1

                except Exception as ex:
                    m_errors += 1
                    issue = (
                        "UNREADABLE_FILE"
                        if isinstance(ex, (PermissionError, OSError))
                        else "ERROR"
                    )
                    reporter.record_quarantine(
                        model=f"{app_label}.{model_name}",
                        pk=str(record.pk),
                        field=field_name,
                        path=str(file_path),
                        issue_type=issue,
                        error=str(ex),
                    )
                    console.print(
                        f"[bold red]Error processing {file_path}: {ex}[/bold red]"
                    )
                    if is_execute and not isinstance(ex, (PermissionError, OSError)):
                        raise

            reporter.record_target(
                target_name=f"{app_label}.{model_name} ({field_name})",
                total_count=count,
                migrated=m_migrated,
                skipped=m_skipped,
                quarantined=m_quarantined,
                conflicts=0,
                errors=m_errors,
            )

        json_path, md_path = reporter.write_reports(output_dir=output_dir)
        reporter.print_summary(console=console)
        console.print(f"\n[bold cyan]Report saved to:[/bold cyan] {json_path}")
        console.print(f"[bold cyan]Markdown summary:[/bold cyan] {md_path}\n")

    def _containerize_file(self, file_path: Path, min_free_disk_mb: int = 50) -> None:
        """Stream plaintext or legacy LFENC01 into LFENC02 container.

        Performs SHA-256 loopback verification before atomic swap.
        """
        tmp_path = file_path.with_suffix(f"{file_path.suffix}.tmp.enc")
        is_verified = False

        try:
            # Pre-flight disk space buffer check (required: double file size + buffer)
            plaintext_size = file_path.stat().st_size
            usage = shutil.disk_usage(file_path.parent)
            required_space = (plaintext_size * 2) + (min_free_disk_mb * 1024 * 1024)
            if usage.free < required_space:
                msg = (
                    f"Insufficient disk space for {file_path}. "
                    f"Required: {required_space} bytes, Available: {usage.free} bytes."
                )
                raise OSError(msg)

            h_orig = hashlib.sha256()
            key_id, key_bytes = EncryptionService._get_key_bytes()
            file_uuid = uuid.uuid4().bytes

            header_bytes, _ = ChunkedContainerEngine.build_header(
                plaintext_size=plaintext_size,
                key_id=key_id,
                chunk_size=DEFAULT_CHUNK_SIZE,
                file_uuid=file_uuid,
                key_bytes=key_bytes,
            )

            with file_path.open("rb") as src_f, tmp_path.open("wb") as dst_f:
                dst_f.write(header_bytes)
                chunk_idx = 0
                while True:
                    chunk = src_f.read(DEFAULT_CHUNK_SIZE)
                    if not chunk:
                        break
                    h_orig.update(chunk)
                    encrypted_chunk = ChunkedContainerEngine.encrypt_chunk(
                        chunk_plaintext=chunk,
                        chunk_index=chunk_idx,
                        file_uuid=file_uuid,
                        key_bytes=key_bytes,
                    )
                    dst_f.write(encrypted_chunk)
                    chunk_idx += 1

            orig_digest = h_orig.digest()

            # Loopback verification
            h_dec = hashlib.sha256()
            with tmp_path.open("rb") as raw_dst:
                reader = EncryptedStreamReader(raw_dst, key_bytes=key_bytes)
                while True:
                    chunk = reader.read(DEFAULT_CHUNK_SIZE)
                    if not chunk:
                        break
                    h_dec.update(chunk)

            dec_digest = h_dec.digest()

            if dec_digest == orig_digest:
                is_verified = True
                tmp_path.replace(file_path)

        finally:
            if tmp_path.exists():
                tmp_path.unlink()

        if not is_verified:
            msg = f"Loopback SHA-256 verification failed for {file_path}"
            raise RuntimeError(msg)

    def _revert_file(self, file_path: Path) -> None:
        """Stream LFENC02 container decrypted payload into plain unencrypted file.

        Performs size verification before atomic swap.
        """
        tmp_path = file_path.with_suffix(f"{file_path.suffix}.tmp.dec")
        is_verified = False

        try:
            _, key_bytes = EncryptionService._get_key_bytes()
            total_decrypted = 0

            with file_path.open("rb") as raw_src, tmp_path.open("wb") as dst_f:
                reader = EncryptedStreamReader(raw_src, key_bytes=key_bytes)
                expected_size = reader.header.plaintext_size
                while True:
                    chunk = reader.read(DEFAULT_CHUNK_SIZE)
                    if not chunk:
                        break
                    dst_f.write(chunk)
                    total_decrypted += len(chunk)

            if total_decrypted == expected_size:
                is_verified = True
                tmp_path.replace(file_path)

        finally:
            if tmp_path.exists():
                tmp_path.unlink()

        if not is_verified:
            msg = f"Decryption size mismatch during reversal for {file_path}"
            raise RuntimeError(msg)
