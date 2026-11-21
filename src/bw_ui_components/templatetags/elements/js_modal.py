# -*- coding: utf-8 -*-#
import json
import ast
from django import template
from django.urls import reverse_lazy
from django.utils.html import format_html

from core.utils import get_request_context, debugging_print

register = template.Library()


@register.inclusion_tag(
    "bw_ui_components/elements/js_modal.html", takes_context=True
)
def bw_js_modal(context, *args, **kwargs) -> dict:
    context_data = get_request_context(context, kwargs)
    url = ""
    action_url = kwargs.get("action_url", None)
    action_url_pk = kwargs.get("action_url_pk", None)
    extra_hidden_inputs = kwargs.get("extra_hidden_inputs", None)
    extra_hidden_inputs_markup_list = []

    # Process extra hidden inputs
    if extra_hidden_inputs is not None:
        extra_hidden_inputs = ast.literal_eval(extra_hidden_inputs)
        for name, value in extra_hidden_inputs.items():
            extra_hidden_inputs_markup_list.append(
                format_html("<input type='hidden' name='{}' value='{}' />", name, value)
            )

    # Modal size (optional, defaults to 'md' for backward compatibility)
    # Size parameter is kept but doesn't affect responsive behavior
    modal_size = kwargs.get("modal_size", "md")

    if action_url is not None:
        url = reverse_lazy(action_url)
        if action_url_pk is not None:
            url = reverse_lazy(action_url, kwargs={"pk": action_url_pk})
        context_data.update({"form_action_url": url})

    context_data.update(
        {"extra_hidden_inputs_markup_list": extra_hidden_inputs_markup_list}
    )

    return {**context_data, **kwargs}
