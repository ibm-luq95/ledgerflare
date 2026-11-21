from typing import Any

from django import forms
from django.utils.translation import gettext as _

PER_PAGE_CHOICES = (
    (10, 10),
    (20, 20),
    (30, 30),
    (50, 50),
    (100, 100),
)


class PerPageForm(forms.Form):
    """
    A Django form for selecting the number of records to display per page.

    Attributes:
    - per_page: ChoiceField representing the number of records per page.

    Methods:
    - __init__(self, *args: Any, **kwargs: Any) -> None: Initializes the form with initial values.

    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initializes the form with initial values.

        Parameters:
        - *args: Variable length argument list.
        - **kwargs: Arbitrary keyword arguments.

        If 'initial' keyword argument is provided, it sets the initial value of 'per_page' field.
        If 'initial' keyword argument is not provided, it sets the initial value to the first choice in PER_PAGE_CHOICES.

        """
        super(PerPageForm, self).__init__(*args, **kwargs)
        if kwargs.get("initial"):
            self.fields["per_page"].initial = kwargs["initial"].get(
                "per_page", PER_PAGE_CHOICES[0][0]
            )
        else:
            self.fields["per_page"].initial = {"per_page": PER_PAGE_CHOICES[0][0]}

    per_page = forms.ChoiceField(
        choices=PER_PAGE_CHOICES,
        label=_("Per page"),
        help_text=_("Records per page"),
        # initial=50,
        required=False,
    )
