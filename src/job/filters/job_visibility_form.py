"""
Form class for toggling job visibility.

This form includes a checkbox to control the display of all jobs within the application.
"""

from __future__ import annotations
from django.utils.translation import gettext as _
from django import forms


class JobVisibilityForm(forms.Form):
    """
    Form enabling global job display toggle.

    Parameters
    ----------
    *args
        Variable length argument list forwarded to parent Form class.
    **kwargs
        Arbitrary keyword arguments forwarded to parent Form class.

    Attributes
    ----------
    show_all_jobs : forms.BooleanField
        Checkbox controlling comprehensive job visibility.

    Examples
    --------
    Instantiate and render the form in a template:

    >>> form = JobVisibilityForm()
    >>> form.as_p()
    '<p><label for="id_show_all_jobs">Show all jobs:</label> ...'
    """

    show_all_jobs: forms.BooleanField = forms.BooleanField(
        label=_("Show all jobs"),
        required=False,
        help_text=_("Check this box to show all jobs"),
        widget=forms.CheckboxInput,
    )
