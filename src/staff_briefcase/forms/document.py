# -*- coding: utf-8 -*-#
from typing import Optional

from django import forms
from django.utils.translation import gettext as _

from core.constants.file_types_validation import IMAGES_AND_DOCS_FT
from core.forms.mixins.base_form_mixin import BWBaseFormMixin
from core.forms.mixins.js_modal_form_renderer_mixin import BWJSModalFormRendererMixin
from core.forms.mixins.remove_fields_mixin import RemoveFieldsMixin
from core.utils import FileValidator


class BriefcaseDocumentMiniForm(
    RemoveFieldsMixin, BWJSModalFormRendererMixin, BWBaseFormMixin
):
    def __init__(self, removed_fields: Optional[list] = None, *args, **kwargs):
        super(BWBaseFormMixin, self).__init__(*args, **kwargs)
        RemoveFieldsMixin.__init__(self, removed_fields=removed_fields)

    title = forms.CharField(label=_("Title"))
    document_file = forms.FileField(
        label=_("Document file"),
        validators=[
            FileValidator(
                max_size=1024 * 1024 * 100,
                content_types=IMAGES_AND_DOCS_FT,
                scan_malware=True,
            )
        ],
    )
    briefcase = forms.UUIDField(widget=forms.HiddenInput)
