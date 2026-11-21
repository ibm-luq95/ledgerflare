# -*- coding: utf-8 -*-#
"""
File: string_helpers_tags.py
Author: Ibrahim Luqman
Date: 5/13/24

Description: All templatetags that handle string processes
"""
from typing import Any, Union, Optional
import inflection
import textwrap
from django import template
from django.template.defaultfilters import stringfilter

from core.constants.general import DEFAULT_TEMPLATE_TABLE_LIST_TRUNCATED_STRING

register = template.Library()


@register.filter(name="to_title_case")
@stringfilter
def to_title_case(text: Union[str, Any]) -> str:
    """
    Converts a string to title case.

    Args:
        text (Union[str, Any]): The input string to be converted.

    Returns:
        str: The converted string in title case.

    """
    return inflection.titleize(str(text))


@register.filter(name="replace_string")
@stringfilter
def replace_string(text: Union[str, None]) -> Union[str, None]:
    """
    Replaces underscores with spaces in the given text.

    Args:
        text (Union[str, None]): The input text to be modified.

    Returns:
        Union[str, None]: The modified text with underscores replaced by spaces, or None if the input is None.

    """
    if text is None:
        return None
    return text.replace("_", " ")


@register.filter(name="bw_truncate_titles")
@stringfilter
def bw_truncate_titles(text: str) -> Optional[str]:
    """
    Truncates a given text to a specified width, replacing the truncated part with a
    placeholder.

    Args:
        text (str): The text to be truncated.

    Returns:
        Optional[str]: The truncated text, or None if the input is None.

    """
    if text is None:
        return None
    return textwrap.shorten(
        text, width=DEFAULT_TEMPLATE_TABLE_LIST_TRUNCATED_STRING, placeholder="..."
    )


@register.filter(name="grab_last_permission_label")
def grab_last_permission_label(permission_full_name: str) -> Optional[str]:
    """
    Grab the last permission label from the full name.

    Args:
        permission_full_name (str): The full name of the permission.

    Returns:
        Optional[str]: The last permission label extracted from the full name, or None if the input is None.

    """
    if permission_full_name is not None:
        return f'{permission_full_name.split(" | ")[0]} - {permission_full_name.split(" | ")[-1]}'
    else:
        return None
