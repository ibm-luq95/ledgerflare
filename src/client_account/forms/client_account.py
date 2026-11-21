# -*- coding: utf-8 -*-#
from typing import Optional

from django import forms

from client_account.models import ClientAccount
from core.constants.form import EXCLUDED_FIELDS
from core.forms import BaseModelFormMixin
from core.forms.mixins.set_field_to_hidden import SetFieldsInputsHiddenMixin
from core.forms.widgets import BWPasswordInputWidget
from core.utils import PasswordHasher


class ClientAccountForm(BaseModelFormMixin, SetFieldsInputsHiddenMixin):
    field_order = [
        "client",
        "service_name",
        "account_name",
        "account_url",
        "account_username",
        "account_password",
    ]

    def __init__(
        self,
        client=None,
        is_update=False,
        updated_object=None,
        hidden_inputs: Optional[dict] = None,
        *args,
        **kwargs,
    ):
        super(ClientAccountForm, self).__init__(*args, **kwargs)
        SetFieldsInputsHiddenMixin.__init__(self, hidden_inputs=hidden_inputs)
        self.is_update = is_update
        self.updated_object = updated_object
        if client is not None:
            # print(self.fields.get("client"))
            self.fields["client"].initial = client

    def clean_client(self):
        client = self.cleaned_data.get("client")
        if self.is_update and self.instance and self.instance.pk:
            if client != self.instance.client:
                raise forms.ValidationError("Client cannot be changed for an existing account.")
        return client

    account_password = forms.CharField(widget=BWPasswordInputWidget, required=False)

    def clean_account_password(self):
        data = self.cleaned_data.get("account_password")
        if (self.is_update or (self.instance and self.instance.pk)) and not data:
            if self.instance and self.instance.account_password:
                return self.instance.account_password
            if self.updated_object and getattr(self.updated_object, "account_password", None):
                return self.updated_object.account_password
        return data

    class Meta(BaseModelFormMixin.Meta):
        model = ClientAccount
        exclude = EXCLUDED_FIELDS
        widgets = {"account_url": forms.URLInput()}
