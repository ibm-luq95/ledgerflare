from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import ObjectDoesNotExist

from beach_wood_user.models import BWUser


class SoftDeleteModelBackend(BaseBackend):
    """
    Custom authentication backend to exclude soft-deleted users.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Use the custom manager to find the user
            user = BWUser.objects.get(email=username, is_deleted=False)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except ObjectDoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            # Use the custom manager to retrieve the user
            return BWUser.objects.get(pk=user_id, is_deleted=False)
        except ObjectDoesNotExist:
            return None

    def user_can_authenticate(self, user):
        """
        Reject users with is_active=False.
        """
        return user.is_active