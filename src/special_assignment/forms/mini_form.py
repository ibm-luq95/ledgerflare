# -*- coding: utf-8 -*-#
from django import forms
from django.utils.translation import gettext as _

from beach_wood_user.models import BWUser
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
from core.forms.widgets import RichHTMLEditorWidget
from core.utils import FileValidator

file_validator = FileValidator(max_size=1024 * 1000, content_types=IMAGES_AND_DOCS_FT)


class MiniSpecialAssignmentForm(BWJSModalFormRendererMixin, BWBaseFormMixin):
    def __init__(self, *args, **kwargs):
        super(BWBaseFormMixin, self).__init__(*args, **kwargs)
        self.fields["assigned_by"].label = ""
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

    assigned_to = forms.ModelChoiceField(
        queryset=BWUser.objects.all(), required=True, label=_("Assigned to")
    )
    start_date = forms.DateField(label=_("Start Date"), required=True)
    due_date = forms.DateField(label=_("Due Date"), required=True)
    title = forms.CharField(label=_("Title"), required=True)
    body = forms.CharField(label=_("Body"), required=True, widget=RichHTMLEditorWidget)
    attachment = forms.FileField(
        label=_("Attachment"), required=False, validators=[file_validator]
    )
    assigned_by = forms.UUIDField(widget=forms.HiddenInput)
    client = forms.UUIDField(widget=forms.HiddenInput, required=False)
    job = forms.UUIDField(widget=forms.HiddenInput, required=False)
