# -*- coding: utf-8 -*-#
from __future__ import annotations

from django import template

from core.utils import get_request_context

register = template.Library()


@register.inclusion_tag("bw_ui_components/discussion/chatbox.html", takes_context=True)
def bw_discussion_chatbox(context, *args, **kwargs) -> dict:
    context_data = get_request_context(context, kwargs)
    return {**context_data, **kwargs}


@register.inclusion_tag("bw_ui_components/discussion/vue_chatbox.html", takes_context=True)
def bw_vue_chatbox(context, *args, **kwargs) -> dict:
    context_data = get_request_context(context, kwargs)
    return {**context_data, **kwargs}
