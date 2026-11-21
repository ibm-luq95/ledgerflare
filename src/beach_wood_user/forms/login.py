"""Login authentication form and custom widgets for Beach Wood staff."""

from __future__ import annotations

from typing import Any

from django import forms
from django.forms.renderers import TemplatesSetting
from django.utils.translation import gettext as _

from core.choices import BeachWoodUserTypeEnum


class FormRenderer(TemplatesSetting):
    """Custom form renderer for login components."""

    form_template_name = "beach_wood_user/widgets/form_snippet.html"


class BWUserTypeRadioSelect(forms.RadioSelect):
    """Custom tactile radio select widget for staff workspace roles."""

    template_name = "beach_wood_user/widgets/user_types.html"
    option_template_name = "beach_wood_user/widgets/radio_option.html"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize radio select widget attributes."""
        super().__init__(*args, **kwargs)
        self.attrs.update({"class": "relative"})


class BWEmailInput(forms.EmailInput):
    """Custom styled email input widget with icon padding and dark theme."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize email input attributes."""
        super().__init__(*args, **kwargs)
        self.attrs.update(
            {
                "class": (
                    "py-2.5 px-3.5 ps-10 block w-full border-zinc-200 "
                    "rounded-xl text-sm text-zinc-900 bg-white "
                    "placeholder:text-zinc-400 focus:border-zinc-900 "
                    "focus:ring-1 focus:ring-zinc-900/10 disabled:opacity-50 "
                    "disabled:pointer-events-none dark:bg-zinc-900/80 "
                    "dark:border-zinc-800 dark:text-zinc-100 "
                    "dark:placeholder:text-zinc-600 dark:focus:border-zinc-400 "
                    "dark:focus:ring-zinc-400/10 shadow-2xs transition-colors"
                ),
                "placeholder": "name@ledgerflare.com",
                "autocomplete": "email",
            }
        )


class BWPasswordInput(forms.PasswordInput):
    """Custom styled password input widget with toggle support and dark theme."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize password input attributes."""
        super().__init__(*args, **kwargs)
        self.attrs.update(
            {
                "class": (
                    "py-2.5 px-3.5 ps-10 pe-10 block w-full border-zinc-200 "
                    "rounded-xl text-sm text-zinc-900 bg-white "
                    "placeholder:text-zinc-400 focus:border-zinc-900 "
                    "focus:ring-1 focus:ring-zinc-900/10 disabled:opacity-50 "
                    "disabled:pointer-events-none dark:bg-zinc-900/80 "
                    "dark:border-zinc-800 dark:text-zinc-100 "
                    "dark:placeholder:text-zinc-600 dark:focus:border-zinc-400 "
                    "dark:focus:ring-zinc-400/10 shadow-2xs transition-colors"
                ),
                "placeholder": "••••••••••••",
                "autocomplete": "current-password",
            }
        )


class BWLoginForm(forms.Form):
    """Authentication login form for Beach Wood staff with role selection."""

    default_renderer = FormRenderer()

    user_type = forms.ChoiceField(
        label=False,
        choices=BeachWoodUserTypeEnum.choices,
        required=True,
        widget=BWUserTypeRadioSelect,
        error_messages={"required": _("User type required!")},
    )
    email = forms.EmailField(
        label="Email Address",
        required=True,
        widget=BWEmailInput,
        error_messages={"required": _("Email address required!")},
    )
    password = forms.CharField(
        widget=BWPasswordInput,
        required=True,
        error_messages={"required": _("Password required!")},
    )
