# -*- coding: utf-8 -*-#
from __future__ import annotations

from typing import Any
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


class CachedViewSetResponseMixin:
    """
    A mixin that applies response caching to list actions of low-volatility reference ViewSets.
    Default cache_timeout is 300 seconds (5 minutes).
    """

    cache_timeout: int = 300

    @method_decorator(cache_page(60 * 5))
    def list(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        return super().list(request, *args, **kwargs)
