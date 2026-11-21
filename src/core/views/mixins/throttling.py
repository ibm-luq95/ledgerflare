"""core/views/mixins/throttling.py - Throttling mixin for Django Class-Based Views"""

from __future__ import annotations
from typing import Type
from django.http import HttpRequest, HttpResponse
from rest_framework.throttling import BaseThrottle
from rest_framework.views import APIView

class ThrottledViewMixin:
    """
    Mixin to enforce DRF throttle classes on standard Django Views / CBVs.
    Returns HTTP 429 Too Many Requests when request limits are exceeded.
    """

    throttle_classes: list[Type[BaseThrottle]] = []

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if self.throttle_classes:
            dummy_view = APIView()
            dummy_view.request = request
            for throttle_class in self.throttle_classes:
                throttle = throttle_class()
                if not throttle.allow_request(request, dummy_view):
                    return HttpResponse(
                        "Too Many Requests. Please slow down.",
                        status=429,
                        content_type="text/plain",
                    )
        return super().dispatch(request, *args, **kwargs)
