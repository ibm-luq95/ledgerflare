# -*- coding: utf-8 -*-#
from __future__ import annotations

import nh3

ALLOWED_TAGS: set[str] = {
    "p",
    "br",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "s",
    "strike",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ol",
    "ul",
    "li",
    "a",
    "span",
    "blockquote",
    "pre",
    "code",
}

ALLOWED_ATTRIBUTES: dict[str, set[str]] = {
    "a": {"href", "title", "target"},
    "span": {"class"},
}

ALLOWED_URL_SCHEMES: set[str] = {"http", "https", "mailto"}


def sanitize_html(html_content: str | None) -> str:
    """
    Sanitizes HTML content using nh3 (Rust ammonia bindings).
    Strips dangerous tags (script, style, iframe), event attributes (onload, onerror),
    and invalid URL schemes (javascript:).
    """
    if not html_content or not isinstance(html_content, str):
        return ""

    return nh3.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_URL_SCHEMES,
        link_rel="noopener noreferrer",
    )
