# -*- coding: utf-8 -*-#
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy


class BWLoginRequiredMixin(LoginRequiredMixin):
    """
    Mixin class that requires the user to be authenticated before accessing the view.

    Attributes:
        login_url (str): The URL to redirect to for login.

    """

    login_url = reverse_lazy("auth:login")

    def dispatch(self, request, *args, **kwargs):
        """Ensure auth_token is stored in session for authenticated users before view execution."""
        if request.user.is_authenticated and not request.session.get("auth_token"):
            from rest_framework.authtoken.models import Token

            token, _ = Token.objects.get_or_create(user=request.user)
            request.session["auth_token"] = token.key
            request.session.modified = True
        return super().dispatch(request, *args, **kwargs)


