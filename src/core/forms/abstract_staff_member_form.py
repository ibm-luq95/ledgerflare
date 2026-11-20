# -*- coding: utf-8 -*-#
from typing import Optional, Dict, List

from django import forms
from django.utils.translation import gettext as _

from core.constants.file_types_validation import IMAGES_FT
from core.forms.mixins.remove_fields_mixin import RemoveFieldsMixin
from core.forms.widgets import RichHTMLEditorWidget, BWPasswordInputWidget
from core.utils import FileValidator

image_validator = FileValidator(
    max_size=15 * 1024 * 1024,
    content_types=IMAGES_FT,
    scan_malware=True,
)


class AbstractStaffMemberForm(forms.Form, RemoveFieldsMixin):
    """
    A form for abstract staff members with fields for user information and profile details.

    Args:
        user_type (str): The type of user.
        removed_fields (Optional[list], optional): The fields to be removed. Defaults to None.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Attributes:
        field_order (list): The order of the fields in the form.
        password (CharField): The password field.
        confirm_password (CharField): The confirm password field.
        email (EmailField): The email field.
        first_name (CharField): The first name field.
        last_name (CharField): The last name field.
        profile_picture (ImageField): The profile picture field.
        address (CharField): The address field.
        phone_number (CharField): The phone number field.
        bio (CharField): The bio field.
        user_type (CharField): The user type field.
        facebook (URLField): The Facebook URL field.
        twitter (URLField): The Twitter URL field.
        github (URLField): The GitHub URL field.
        linkedin (URLField): The LinkedIn URL field.
        instagram (URLField): The Instagram URL field.

    Methods:
        clean_confirm_password(): Validates that the password and confirm password fields match.
        split_user_profiles_inputs(excluded_fields: Optional[list] = []): Splits the form inputs into user and profile sections.

    Meta:
        abstract = True

    """

    def __init__(
        self, user_type: str, removed_fields: Optional[list] = None, *args, **kwargs
    ):
        """
        Initializes the form with the given parameters.

        Args:
            user_type (str): The type of user.
            removed_fields (Optional[list], optional): The fields to be removed. Defaults to None.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        """
        # Call the parent class's constructor
        super().__init__(*args, **kwargs)

        # Initialize the RemoveFieldsMixin
        RemoveFieldsMixin.__init__(self, removed_fields=removed_fields)

        # Set the initial value of the 'user_type' field
        self.fields.get("user_type").initial = user_type

        # Set the 'data-block-section' attribute for the 'password' field
        if self.fields.get("password"):
            self.fields.get("password").widget.attrs["data-block-section"] = "user"

        # Set the 'data-block-section' attribute for the 'confirm_password' field
        if self.fields.get("confirm_password"):
            self.fields.get("confirm_password").widget.attrs["data-block-section"] = "user"

        # Set the 'data-block-section' attribute for the 'user_type' field
        self.fields.get("user_type").widget.attrs["data-block-section"] = "user"

        # Set the 'data-block-section' attribute for the 'email' field
        self.fields.get("email").widget.attrs["data-block-section"] = "user"

        # Set the 'data-block-section' attribute for the 'first_name' field
        self.fields.get("first_name").widget.attrs["data-block-section"] = "user"

        # Set the 'data-block-section' attribute for the 'last_name' field
        self.fields.get("last_name").widget.attrs["data-block-section"] = "user"

        # Set the 'data-block-section' attribute for the 'user_type' field
        self.fields.get("user_type").widget.attrs["data-block-section"] = "user"

        # Set the 'data-block-section' attribute for the 'profile_picture' field
        if self.fields.get("profile_picture"):
            self.fields.get("profile_picture").widget.attrs[
                "data-block-section"
            ] = "profile"

        # Set the 'data-block-section' attribute for the 'facebook' field
        self.fields.get("facebook").widget.attrs["data-block-section"] = "profile"

        # Set the 'data-block-section' attribute for the 'twitter' field
        self.fields.get("twitter").widget.attrs["data-block-section"] = "profile"

        # Set the 'data-block-section' attribute for the 'github' field
        self.fields.get("github").widget.attrs["data-block-section"] = "profile"

        # Set the 'data-block-section' attribute for the 'linkedin' field
        self.fields.get("linkedin").widget.attrs["data-block-section"] = "profile"

        # Set the 'data-block-section' attribute for the 'instagram' field
        self.fields.get("instagram").widget.attrs["data-block-section"] = "profile"

    field_order = [
        "first_name",
        "last_name",
        "email",
        "password",
        "confirm_password",
        "profile_picture",
    ]
    password = forms.CharField(
        label=_("Password"), required=False, widget=BWPasswordInputWidget
    )
    confirm_password = forms.CharField(
        label=_("Confirm Password"), required=False, widget=BWPasswordInputWidget
    )
    email = forms.EmailField(label=_("Email Address"), required=True)
    first_name = forms.CharField(label=_("First Name"), required=True)
    last_name = forms.CharField(label=_("Last Name"), required=True)
    profile_picture = forms.ImageField(
        label=_("Profile Picture"), required=False, validators=[image_validator]
    )
    address = forms.CharField(label=_("Address"), required=False)
    phone_number = forms.CharField(label=_("Phone number"), required=False)
    bio = forms.CharField(label=_("BIO"), widget=RichHTMLEditorWidget, required=False)
    user_type = forms.CharField(label="", widget=forms.HiddenInput, required=False)
    facebook = forms.URLField(label=_("Facebook"), required=False)
    twitter = forms.URLField(label=_("Twitter"), required=False)
    github = forms.URLField(label=_("Github"), required=False)
    linkedin = forms.URLField(label=_("Linkedin"), required=False)
    instagram = forms.URLField(label=_("Instagram"), required=False)

    class Meta:
        abstract = True

    def clean_confirm_password(self) -> Optional[str]:
        """
        Validates that the password and confirm password fields match.

        Args:
            self: The form instance.

        Returns:
            Optional[str]: The confirmed password if it matches the password field, else None.

        """
        password: Optional[str] = self.cleaned_data.get("password")
        confirm_password: Optional[str] = self.cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise forms.ValidationError(
                _("Password confirmation does not match!"), code="invalid"
            )
        return confirm_password

    def split_user_profiles_inputs(
        self, excluded_fields: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Optional[str]]]:
        """
        Splits the form inputs into user and profile sections.

        Args:
            excluded_fields (Optional[List[str]], optional): The fields to be excluded. Defaults to None.

        Returns:
            Dict[str, Dict[str, Optional[str]]]: A dictionary containing the user and profile inputs.

        """
        inputs: Dict[str, Dict[str, Optional[str]]] = {"user": {}, "profile": {}}
        for field_name, field in self.fields.items():
            if field_name not in excluded_fields:
                section = field.widget.attrs.get("data-block-section")
                if section == "user":
                    inputs["user"][field_name] = self.cleaned_data.get(field_name)
                elif section == "profile":
                    inputs["profile"][field_name] = self.cleaned_data.get(field_name)
        return inputs
