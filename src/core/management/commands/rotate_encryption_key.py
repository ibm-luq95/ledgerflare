"""Command to re-encrypt model fields across key versions."""

from __future__ import annotations

import logging
from typing import Any

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import models, transaction

from core.crypto.service import (
    DecryptionIntegrityError,
    EncryptionService,
    KeyConfigurationError,
)
from core.fields.encrypted_fields import EncryptedFieldMixin
from core.models.fields.encrypted_field import (
    EncryptedCharField as LegacyEncryptedCharField,
)


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Re-encrypt model fields across key versions in atomic batches."""

    help = "Re-encrypt model fields across key versions in atomic batches."

    def add_arguments(self, parser: Any) -> None:
        """Configure command line arguments."""
        parser.add_argument(
            "--from-key",
            type=str,
            default=None,
            help="Source key ID to rotate from (e.g. k1 or legacy).",
        )
        parser.add_argument(
            "--to-key",
            type=str,
            default=None,
            help="Target key ID to re-encrypt into (defaults to ACTIVE_KEY_ID).",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of records per atomic database transaction (default 100).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Scan and report records needing rotation without writing changes.",
        )
        parser.add_argument(
            "--app",
            type=str,
            default=None,
            help="Restrict rotation to a specific app label.",
        )
        parser.add_argument(
            "--model",
            type=str,
            default=None,
            help="Restrict rotation to a specific model name.",
        )

    def _discover_targets(
        self, app_filter: str | None, model_filter: str | None
    ) -> list[tuple[type[models.Model], list[models.Field]]]:
        """Discover concrete models and fields that require encryption management."""
        targets: list[tuple[type[models.Model], list[models.Field]]] = []
        for model in apps.get_models():
            if model._meta.proxy or model._meta.abstract or not model._meta.managed:
                continue

            if app_filter and model._meta.app_label.lower() != app_filter.lower():
                continue

            if model_filter and model._meta.model_name.lower() != model_filter.lower():
                continue

            enc_fields = [
                field
                for field in model._meta.get_fields()
                if isinstance(field, (EncryptedFieldMixin, LegacyEncryptedCharField))
            ]

            if enc_fields:
                targets.append((model, enc_fields))

        return targets

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute rotation process across target models."""
        from_key: str | None = options.get("from_key")
        to_key: str = options.get("to_key") or getattr(settings, "ACTIVE_KEY_ID", "k1")
        batch_size: int = options.get("batch_size", 100)
        dry_run: bool = options.get("dry_run", False)
        app_filter: str | None = options.get("app")
        model_filter: str | None = options.get("model")

        mode_str = "DRY RUN - SCAN ONLY" if dry_run else "LIVE ROTATION"
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Starting Key Rotation: {mode_str} (Target key: {to_key})"
            )
        )

        targets = self._discover_targets(app_filter, model_filter)
        if not targets:
            self.stdout.write(
                self.style.WARNING("No encrypted models found matching filters.")
            )
            return

        total_scanned = 0
        total_rotated = 0
        total_skipped = 0
        total_failed = 0

        target_prefix = f"v1:{to_key}:"
        from_prefix = f"v1:{from_key}:" if from_key and from_key != "legacy" else None

        for model, enc_fields in targets:
            model_name = model._meta.model_name
            concrete_model = getattr(model._meta, "concrete_model", model)
            actual_model_name = concrete_model._meta.model_name

            if hasattr(model, "original_objects"):
                manager = model.original_objects
            elif hasattr(model, "_objects"):
                manager = model._objects
            else:
                manager = model.objects

            self.stdout.write(
                f"\nProcessing {model._meta.label} ({len(enc_fields)} field(s))..."
            )

            field_attnames = [f.attname for f in enc_fields]
            last_pk = None

            while True:
                qs = manager.all().order_by("pk")
                if last_pk is not None:
                    qs = qs.filter(pk__gt=last_pk)

                batch_records = list(qs[:batch_size])
                if not batch_records:
                    break

                batch_pks = [r.pk for r in batch_records]
                last_pk = batch_pks[-1]

                # Single bulk query for raw ciphertext dictionary of the batch
                raw_dict_map = {
                    item["pk"]: item
                    for item in manager.filter(pk__in=batch_pks).values(
                        "pk", *field_attnames
                    )
                }

                with transaction.atomic():
                    for record in batch_records:
                        total_scanned += 1
                        record_pk_str = str(record.pk)
                        raw_dict = raw_dict_map.get(record.pk, {})
                        record_updates: dict[str, str] = {}
                        has_failure = False

                        for field in enc_fields:
                            field_name = field.attname
                            raw_val = raw_dict.get(field_name)

                            if not raw_val or not isinstance(raw_val, str):
                                total_skipped += 1
                                continue

                            needs_rotation = False
                            if raw_val.startswith(target_prefix):
                                total_skipped += 1
                                continue

                            if from_key == "legacy":
                                needs_rotation = raw_val.startswith(("v2$", "gAAAAA"))
                            elif from_prefix:
                                needs_rotation = raw_val.startswith(from_prefix)
                            else:
                                needs_rotation = True

                            if not needs_rotation:
                                total_skipped += 1
                                continue

                            aad = (
                                f"{actual_model_name}:{field_name}:{record_pk_str}"
                            ).encode()
                            try:
                                decrypted = EncryptionService.decrypt(raw_val, aad)
                                new_ciphertext = EncryptionService.encrypt(
                                    decrypted, aad, key_id=to_key
                                )
                                record_updates[field_name] = new_ciphertext
                            except (
                                DecryptionIntegrityError,
                                KeyConfigurationError,
                                ValueError,
                                TypeError,
                            ) as err:
                                has_failure = True
                                total_failed += 1
                                self.stderr.write(
                                    self.style.ERROR(
                                        f"Failed decrypting {model_name}.{field_name} "
                                        f"(PK: {record_pk_str}): {err}"
                                    )
                                )
                                continue

                        if record_updates and not dry_run:
                            manager.filter(pk=record.pk).update(**record_updates)

                        if record_updates and not has_failure:
                            total_rotated += 1

        summary = (
            f"\nKey Rotation Complete:\n"
            f"  Total Scanned: {total_scanned}\n"
            f"  Total Rotated: {total_rotated}\n"
            f"  Total Skipped: {total_skipped}\n"
            f"  Total Failed:  {total_failed}\n"
        )
        if total_failed > 0:
            self.stdout.write(self.style.WARNING(summary))
        else:
            self.stdout.write(self.style.SUCCESS(summary))
