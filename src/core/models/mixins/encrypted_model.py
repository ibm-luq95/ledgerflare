"""Model mixin providing integrity checks and blind index lookups."""

from __future__ import annotations

from core.crypto.service import DecryptionIntegrityError
from core.fields.encrypted_fields import EncryptedCharField, EncryptedTextField


class EncryptedModelMixin:
    """Mixin for models containing encrypted fields to verify tamper resistance."""

    def verify_record_integrity(self) -> bool:
        """Verify that all encrypted fields decrypt successfully against record AAD."""
        for field in self._meta.fields:  # type: ignore[attr-defined]
            if isinstance(field, (EncryptedTextField, EncryptedCharField)):
                try:
                    val = getattr(self, field.attname)
                    if val is not None and not isinstance(val, str):
                        return False
                except DecryptionIntegrityError, ValueError, TypeError:
                    return False
        return True

    @classmethod
    def get_blind_index_query(
        cls, field_name: str, search_value: str, normalize: bool = True
    ) -> dict[str, str]:
        """Generate query dictionary for exact search via blind index."""
        from core.crypto.blind_index import compute_blind_index

        concrete = getattr(cls._meta, "concrete_model", None)
        model_name = (concrete or cls)._meta.model_name
        context = f"{model_name}:{field_name}"
        bidx = compute_blind_index(search_value, context=context, normalize=normalize)
        return {f"{field_name}_bidx": bidx}
