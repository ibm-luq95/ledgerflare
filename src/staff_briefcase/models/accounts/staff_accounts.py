from __future__ import annotations

from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils.translation import gettext as _

from core.choices import ServiceNameEnum
from core.fields.encrypted_fields import EncryptedCharField, EncryptedTextField
from core.models.mixins import BaseModelMixin, StrModelMixin


class StaffAccounts(BaseModelMixin, StrModelMixin):
    """Represents a staff account with encrypted password storage."""

    title = models.CharField(_("title"), max_length=150)
    url = EncryptedTextField(
        _("url"),
        null=True,
        blank=True,
        trigram_blind_index=True,
        blind_index_field="url_bidx",
    )
    url_bidx = ArrayField(
        models.CharField(max_length=16),
        default=list,
        blank=True,
        help_text=_("Trigram blind index tokens for partial URL searching."),
    )
    username_email = EncryptedCharField(
        _("Username / Email"),
        max_length=512,
        trigram_blind_index=True,
        blind_index_field="username_email_bidx",
    )
    username_email_bidx = ArrayField(
        models.CharField(max_length=16),
        default=list,
        blank=True,
        help_text=_("Trigram blind index tokens for partial username searching."),
    )
    password = EncryptedCharField(_("Password"), max_length=500, null=True, blank=True)
    name = models.CharField(
        _("name"),
        max_length=35,
        choices=ServiceNameEnum.choices,
        null=True,
        blank=True,
    )

    class Meta(BaseModelMixin.Meta):
        ordering = ["title"]
        indexes = [
            *BaseModelMixin.Meta.indexes,
            models.Index(name="staff_account_name_idx", fields=["name"]),
            models.Index(name="staff_account_title_idx", fields=["title"]),
            GinIndex(fields=["username_email_bidx"], name="idx_stf_acc_user_trigram"),
            GinIndex(fields=["url_bidx"], name="idx_stf_acc_url_trigram"),
        ]

    @property
    def decrypted_password(self) -> str | None:
        """Alias property returning password for backward compatibility."""
        return self.password

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
