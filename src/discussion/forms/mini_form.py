# -*- coding: utf-8 -*-#
from typing import Optional

from django import forms
from django.utils.translation import gettext as _

from core.constants.file_types_validation import IMAGES_AND_DOCS_FT
from core.constants.form import (
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
from core.forms.mixins.base_form_mixin import BWBaseFormMixin
from core.forms.mixins.js_modal_form_renderer_mixin import BWJSModalFormRendererMixin
from core.forms.mixins.remove_fields_mixin import RemoveFieldsMixin
from core.forms.mixins.staff_member_form_mixin import BWStaffMemberFormMixin
from core.forms.widgets import RichHTMLEditorWidget
from core.utils import FileValidator
from job.models import JobProxy
from special_assignment.models import SpecialAssignmentProxy

file_validator = FileValidator(max_size=1024 * 1000, content_types=IMAGES_AND_DOCS_FT)


class DiscussionMiniForm(
    BWJSModalFormRendererMixin, RemoveFieldsMixin, BWStaffMemberFormMixin, BWBaseFormMixin
):
    def __init__(self, removed_fields: Optional[list] = None, *args, **kwargs):
        super(BWBaseFormMixin, self).__init__(*args, **kwargs)
        BWStaffMemberFormMixin.__init__(self, *args, **kwargs)
        RemoveFieldsMixin.__init__(self, removed_fields=removed_fields)
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

    body = forms.CharField(label=_("Body"), required=True, widget=RichHTMLEditorWidget)
    attachment = forms.FileField(
        label=_("Attachment"), required=False, validators=[file_validator]
    )
    job = forms.ModelChoiceField(
        queryset=JobProxy.objects.all(), required=False, widget=forms.HiddenInput
    )
    special_assignment = forms.ModelChoiceField(
        queryset=SpecialAssignmentProxy.objects.all(),
        required=False,
        widget=forms.HiddenInput,
    )
    sender = forms.UUIDField(label=_("Sender"), required=False, widget=forms.HiddenInput)
