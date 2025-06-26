# -*- coding: utf-8 -*-#
from typing import Optional

from django import forms
from django.db import transaction
from django.forms import CheckboxSelectMultiple
from django.forms.utils import flatatt
from django.utils.safestring import mark_safe

from client.models import ClientProxy
from core.constants.css_classes import BW_PRELINE_CHECKBOX_CSS_CLASSES
from core.forms import BaseModelFormMixin

from django.utils.html import format_html, format_html_join

from core.forms.mixins.remove_fields_mixin import RemoveFieldsMixin
from core.forms.widgets import RichHTMLEditorWidget
from core.utils import debugging_print


class CustomCheckboxSelectMultiple(CheckboxSelectMultiple):
    def __init__(self, attrs=None, choices=()):
        super().__init__(attrs=attrs, choices=choices)

    def get_context(self, name, value, attrs=None):
        # Call the base implementation first to get a context
        context = super().get_context(name, value, attrs)

        return context

    def render(self, name, value, attrs=None, renderer=None):
        final_code = super().render(name, value, attrs)
        debugging_print(final_code)
        if value is None:
            value = []
        has_id = attrs and "id" in attrs
        final_attrs = self.build_attrs(attrs, extra_attrs={"class": "flex"})
        input_html = []
        debugging_print(final_attrs)
        # debugging_print(locals())

        for i, choice in enumerate(self.choices):
            choice_value, choice_label = choice
            # debugging_print(choice_value)
            # debugging_print(choice_label)
            checked = choice_value in value
            attrs.update({"class": BW_PRELINE_CHECKBOX_CSS_CLASSES})
            # debugging_print(attrs)
            input_attrs = dict(attrs, type=self.input_type, name=name, value=choice_value)
            if checked:
                input_attrs["checked"] = "checked"
            input_html.append(
                format_html(
                    "<input{} />",
                    format_html_join("", ' {}="{}"', sorted(input_attrs.items())),
                )
            )

            input_html.append(
                format_html(
                    '<label class="checkbox-label" for="{}">{}</label>',
                    attrs["id"] + "_" + str(i),
                    choice_label,
                )
            )

        final_code = format_html(
            "<div{}>\n{}\n</div><br />",
            format_html_join("", ' {}="{}"', sorted(final_attrs.items())),
            "\n".join(input_html),
        )
        mark_safe(final_code)
        debugging_print(final_code)
        return final_code


class ClientForm(BaseModelFormMixin, RemoveFieldsMixin):
    field_order = ["name", "email", "categories", "bookkeepers", "important_contacts"]

    def __init__(self, removed_fields: Optional[list] = None, *args, **kwargs):
        super(ClientForm, self).__init__(*args, **kwargs)
        RemoveFieldsMixin.__init__(self, removed_fields=removed_fields)
        self.fields.pop("is_active")

        # if user:
        #     if user.user_type == "assistant":
        #         check_permission = user.has_perm(
        #             "assistant.can_assign_bookkeeper_to_client"
        #         )
        #         if check_permission is False:
        #             self.fields.get("bookkeepers").widget.attrs.setdefault(
        #                 "disabled", "disabled"
        #             )
        #             help_txt = (
        #                 "<strong class='has-text-danger'>**You dont have permission to assign bookkeeper to "
        #                 "this client,contact administrator for more details **</strong>"
        #             )
        #
        #             self.fields.get("bookkeepers").help_text = mark_safe(help_txt)

    class Meta(BaseModelFormMixin.Meta):
        model = ClientProxy
        # fields = "__all__"
        widgets = {
            "bookkeepers": forms.CheckboxSelectMultiple(),
            "cfos": forms.CheckboxSelectMultiple(),
            "important_contacts": forms.CheckboxSelectMultiple(),
            # "categories": CustomCheckboxSelectMultiple(),
            "categories": forms.CheckboxSelectMultiple(),
            "description": RichHTMLEditorWidget(),
        }

    def save(self, commit=True):
        # Save the provided password in hashed format
        client = super().save(commit=False)
        with transaction.atomic():
            if commit:
                client.save()
            self.save_m2m()
            return client
