from typing import Optional

from django import forms
from django.utils import timezone
from django.utils.translation import gettext as _

from core.constants.file_types_validation import IMAGES_FT
from core.constants.status_labels import CON_NOT_STARTED
from core.forms.mixins.base_form_mixin import BWBaseFormMixin
from core.forms.mixins.js_modal_form_renderer_mixin import BWJSModalFormRendererMixin
from core.forms.mixins.remove_fields_mixin import RemoveFieldsMixin
from core.utils import FileValidator


file_validator = FileValidator(max_size=1024 * 1000, content_types=IMAGES_FT)


class ImportantContactMiniForm(
    RemoveFieldsMixin, BWJSModalFormRendererMixin, BWBaseFormMixin
):
    def __init__(self, removed_fields: list | None = None, *args, **kwargs):
        super(BWBaseFormMixin, self).__init__(*args, **kwargs)
        RemoveFieldsMixin.__init__(self, removed_fields=removed_fields)

    client = forms.UUIDField(widget=forms.HiddenInput)
