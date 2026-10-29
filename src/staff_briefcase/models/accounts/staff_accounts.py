from __future__ import annotations

from django.db import models
from django.utils.translation import gettext as _

from core.choices import ServiceNameEnum
from core.fields.encrypted_fields import EncryptedCharField
from core.models.mixins import BaseModelMixin, StrModelMixin


class StaffAccounts(BaseModelMixin, StrModelMixin):
    """Represents a staff account with encrypted password storage."""

    title = models.CharField(_("title"), max_length=150)
    url = models.TextField(_("url"), null=True, blank=True)
    username_email = models.CharField(_("Username / Email"), max_length=150)
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
            models.Index(name="staff_account_name_idx", fields=["name"]),
            models.Index(name="staff_account_title_idx", fields=["title"]),
            models.Index(name="staff_account_username_idx", fields=["username_email"]),
        ]

    @property
    def decrypted_password(self) -> str | None:
        """Alias property returning password for backward compatibility."""
        return self.password

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
