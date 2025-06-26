# -*- coding: utf-8 -*-#
# from client.models import Client
from core.forms import BaseModelFormMixin
from django import forms
from important_contact.models import ImportantContact


class ImportantContactForm(BaseModelFormMixin):
    # auto_id = "important_contact_%s"

    def __init__(
        self,
        is_readonly=False,
        client_pk=None,
        is_creating=False,
        remove_client_field=False,
        created_by=None,
        *args,
        **kwargs,
    ):
        super(ImportantContactForm, self).__init__(*args, **kwargs)
        # print(is_creating)

        if created_by is not None:
            self.created_by = created_by

        if is_readonly is True:
            for field in self.fields:
                self.fields[field].widget.attrs.update({"readonly": "readonly"})
            self.fields["contact_label"].widget.attrs.update(
                {"class": "readonly-select cursor-not-allowed"}
            )

        # check if the client passed in the arguments
        # if client_pk is not None:
        #     self.fields["client"].initial = (
        #         Client.objects.select_related().filter(pk=client_pk).first()
        #     )

        # remove client input
        # if remove_client_field is True:
        #     self.fields.pop("client")

    class Meta(BaseModelFormMixin.Meta):
        model = ImportantContact
        widgets = {
            "contact_postcode": forms.NumberInput(attrs={"placeholder": "e.g. 12345"})
        }
