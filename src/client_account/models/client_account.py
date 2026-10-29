from __future__ import annotations

from django.db import models
from django.utils.translation import gettext as _

from client.models import ClientProxy
from core.choices import ClientAccountStatusEnum, ServiceNameEnum
from core.fields.encrypted_fields import EncryptedCharField
from core.models.mixins import BaseModelMixin


class ClientAccount(BaseModelMixin):
    """Client account model related with client."""

    client = models.ForeignKey(
        to=ClientProxy,
        on_delete=models.RESTRICT,
        null=True,
        related_name="client_accounts",
        blank=True,
    )
    is_services = models.BooleanField(_("is services"), default=False, editable=False)
    account_name = models.CharField(_("account name"), max_length=100, null=True)
    account_url = models.TextField(_("account url"), null=True)
    account_username = models.CharField(_("account username"), max_length=250, null=True)
    account_password = EncryptedCharField(
        _("account password"), max_length=500, null=True, blank=True
    )
    status = models.CharField(
        _("status"),
        max_length=10,
        choices=ClientAccountStatusEnum.choices,
        default=ClientAccountStatusEnum.ENABLED,
    )
    service_name = models.CharField(
        _("service name"),
        max_length=35,
        choices=ServiceNameEnum.choices,
        db_index=True,
        null=True,
        blank=True,
    )
    last_modified_date = models.DateTimeField(_("last_modified_date"), auto_now=True)

    class Meta(BaseModelMixin.Meta):
        ordering = ["account_name"]

    def __str__(self) -> str:
        return f"{self.account_name}"

    @property
    def decrypted_account_password(self) -> str | None:
        """Alias property returning account_password for backward compatibility."""
        return self.account_password

    def save(self, *args, **kwargs):
        if self.service_name != "":
            self.is_services = True
        super().save(*args, **kwargs)
