# -*- coding: utf-8 -*-#
from django import forms
from django.db import transaction

from assistant.models import AssistantProxy
from bookkeeper.models import BookkeeperProxy
from client.models import ClientProxy
from core.constants.form import (
    EXCLUDED_FIELDS,
    PDF_MIME_TYPE,
    DOCX_MIME_TYPE,
    DOC_MIME_TYPE,
    CSV_MIME_TYPE,
    PNG_MIME_TYPE,
    JPEG_MIME_TYPE,
    JPG_MIME_TYPE,
    WEBP_MIME_TYPE,
    AVIF_MIME_TYPE,
    PPT_MIME_TYPE,
    PPTX_MIME_TYPE,
)
from core.forms import BaseModelFormMixin, JoditFormMixin
from core.forms.widgets import RichHTMLEditorWidget
from core.utils import debugging_print
from core.utils.developments.debugging_print_object import DebuggingPrint
from job.models import JobProxy
from manager.models import ManagerProxy
from special_assignment.models import SpecialAssignmentProxy


class SpecialAssignmentForm(BaseModelFormMixin, JoditFormMixin):
    field_order = [
        "assigned_to",
        "client",
        "job",
        "title",
        "body",
        "attachment",
        "start_date",
        "due_date",
        "notes",
        "status",
        "assigned_by",
    ]

    def __init__(self, add_jodit_css_class=False, *args, **kwargs):
        super(SpecialAssignmentForm, self).__init__(*args, **kwargs)
        JoditFormMixin.__init__(self, add_jodit_css_class=add_jodit_css_class)
        # self.fields["client"].queryset = ClientProxy.objects.all().order_by("name")
        # self.fields["job"].queryset = JobProxy.objects.all().order_by("title")
        # self.fields["bookkeeper"].queryset = BookkeeperProxy.objects.all().order_by("user__first_name")
        # self.fields["assistant"].queryset = AssistantProxy.objects.all().order_by("user__first_name")
        # self.fields["manager"].queryset = ManagerProxy.objects.all().order_by("user__first_name")
        # self.fields["assigned_by"].initial = assigned_by
        # self.fields["assigned_by"].widget.attrs.update(
        #     {"class": "readonly-select cursor-not-allowed", "readonly": "readonly"}
        # )
        self.fields.pop("bookkeeper")
        self.fields.pop("manager")
        self.fields.pop("assistant")
        self.fields.get("attachment").widget.attrs.update(
            {
                "accept": (
                    f"{PDF_MIME_TYPE}, {DOCX_MIME_TYPE}, {DOC_MIME_TYPE}, {CSV_MIME_TYPE},"
                    f" {PNG_MIME_TYPE}, {JPEG_MIME_TYPE}, {JPG_MIME_TYPE},"
                    f" {PPTX_MIME_TYPE}, {PPT_MIME_TYPE}, {AVIF_MIME_TYPE},"
                    f" {WEBP_MIME_TYPE}"
                )
            }
        )

    class Meta(BaseModelFormMixin.Meta):
        model = SpecialAssignmentProxy
        exclude = EXCLUDED_FIELDS + ["is_seen"]
        widgets = {"body": RichHTMLEditorWidget, "notes": RichHTMLEditorWidget}

    def save(self, commit=True):
        sa = super().save(commit=False)
        with transaction.atomic():
            DebuggingPrint.pprint(self.cleaned_data)
            if self.cleaned_data.get("job") and not self.cleaned_data.get("client"):
                client = self.cleaned_data.get("job").client
                sa.client = client
            DebuggingPrint.pprint(self.cleaned_data)
            if commit:
                assigned_by = self.initial.get("assigned_by", None)
                if assigned_by is not None:
                    sa.assigned_by = assigned_by
                sa.save()
                self.save_m2m()
            return sa
