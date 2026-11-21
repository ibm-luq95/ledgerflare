# -*- coding: utf-8 -*-#
from typing import Optional

from django import forms
from django.utils.translation import gettext as _

from core.choices import ServiceNameEnum
from core.forms.mixins.base_form_mixin import BWBaseFormMixin
from core.forms.mixins.js_modal_form_renderer_mixin import BWJSModalFormRendererMixin
from core.forms.mixins.remove_fields_mixin import RemoveFieldsMixin
from core.forms.widgets import BWPasswordInputWidget


class BriefcaseAccountMiniForm(
    RemoveFieldsMixin, BWJSModalFormRendererMixin, BWBaseFormMixin
):
    field_order = ["name", "title", "url", "username_email", "password"]

    def __init__(self, removed_fields: Optional[list] = None, *args, **kwargs):
        super(BWBaseFormMixin, self).__init__(*args, **kwargs)
        RemoveFieldsMixin.__init__(self, removed_fields=removed_fields)

    title = forms.CharField(label=_("Title"))
    url = forms.CharField(label=_("URL"), widget=forms.URLInput, required=False)
    username_email = forms.CharField(label=_("Username / Email"), required=False)
    password = forms.CharField(widget=BWPasswordInputWidget, required=False)
    name = forms.ChoiceField(
        label=_("Service Name"),
        choices=[("", _("--- Select Service (Optional) ---"))] + list(ServiceNameEnum.choices),
        required=False,
    )
    briefcase = forms.UUIDField(widget=forms.HiddenInput)
