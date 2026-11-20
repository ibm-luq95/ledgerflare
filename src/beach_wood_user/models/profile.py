# -*- coding: utf-8 -*-#
from PIL import Image
from django.db import models
from django.utils.translation import gettext as _
from django.core.validators import RegexValidator

from core.constants.file_types_validation import IMAGES_FT
from core.models.mixins.base_model import BaseModelMixin
from core.models.mixins.sanitize_html import SanitizeHTMLFieldsMixin
from core.models.mixins.staff_member_social_media import StaffMemberSocialMediaMixin
from core.utils import FileValidator

file_validator = FileValidator(
	max_size=1024 * 1024 * 15,
	content_types=IMAGES_FT,
	scan_malware=True,
)


class Profile(BaseModelMixin, SanitizeHTMLFieldsMixin, StaffMemberSocialMediaMixin, models.Model):
	SANITY_HTML_FIELDS = ("bio",)
	profile_picture = models.ImageField(
		_("profile picture"),
		upload_to="profile_pictures/",
		null=True,
		blank=True,
		validators=[file_validator],
	)
	address = models.CharField(_("address"), max_length=50, null=True, blank=True)
	phone_number = models.CharField(
		_("phone number"),
		max_length=50,
		null=True,
		blank=True,
		validators=[
			RegexValidator(
				regex=r"(?:([+]\d{1,4})[-.\s]?)?(?:[(](\d{1,3})[)][-.\s]?)?(\d{1,4})[-.\s]?(\d{1,4})[-.\s]?(\d{1,9})",
				# Customize the regex pattern as per your phone number format
				message=_(
					"Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
				),
				code="invalid_registration",
			)
		],
	)
	bio = models.TextField(_("bio"), null=True, blank=True)

	def save(self, *args, **kwargs) -> None:
		super(Profile, self).save(*args, **kwargs)
		if self.profile_picture:
			image = Image.open(self.profile_picture.path)
			if image.height > 120 or image.width > 120:
				output_size = (120, 120)
				image.thumbnail(output_size)
				image.save(self.profile_picture.path)

	# def __str__(self) -> str:
	# 	if hasattr(self, "bookkeeper"):
	# 		return _(
	# 			f"Profile for: {self.bookkeeper.user.fullname} - {self.bookkeeper.user.user_type}"
	# 		)
	# 	elif hasattr(self, "assistant"):
	# 		return _(
	# 			f"Profile for: {self.assistant.user.fullname} - {self.assistant.user.user_type}"
	# 		)
	# 	elif hasattr(self, "manager"):
	# 		return _(
	# 			f"Profile for: {self.manager.user.fullname} - {self.manager.user.user_type}"
	# 		)
