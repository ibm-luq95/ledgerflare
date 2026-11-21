# -*- coding: utf-8 -*-#
from typing import Optional

from django import forms


class RichHTMLEditorWidget(forms.widgets.Textarea):
    """
    Widget class for a rich HTML editor that inherits from Textarea widget.

    Attributes:
        attrs (Optional[dict]): Optional attributes for the rich HTML editor widget.

    """

    def __init__(self, attrs: Optional[dict] = None, *args, **kwargs):
        """
        Initializes the RichHTMLEditorWidget instance.

        Args:
            attrs: Optional attributes for the rich HTML editor widget. Defaults to None.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        """
        attrs = attrs or {}
        attrs.update({"class": "wyswyg-editor rich-editor"})
        super(RichHTMLEditorWidget, self).__init__(attrs)
