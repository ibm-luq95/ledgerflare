from __future__ import annotations
from rest_framework.throttling import SimpleRateThrottle

class AuthEndpointRateThrottle(SimpleRateThrottle):
    scope = "auth_endpoint"

    def get_cache_key(self, request, view):
        user = getattr(request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            ident = str(user.pk)
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}

class ExportDataRateThrottle(SimpleRateThrottle):
    scope = "export_data"

    def get_cache_key(self, request, view):
        user = getattr(request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            ident = str(user.pk)
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
