# -*- coding: utf-8 -*-#
from __future__ import annotations

import pytest
from django.conf import settings


@pytest.mark.django_db
def test_drf_global_features_configured() -> None:
    rf = settings.REST_FRAMEWORK
    assert "DEFAULT_PAGINATION_CLASS" in rf
    assert rf.get("PAGE_SIZE") == 25
    assert "DEFAULT_FILTER_BACKENDS" in rf
    assert "DEFAULT_THROTTLE_CLASSES" in rf
    assert "DEFAULT_THROTTLE_RATES" in rf
    assert rf["DEFAULT_THROTTLE_RATES"].get("anon") == "20/minute"
    assert rf["DEFAULT_THROTTLE_RATES"].get("user") == "100/minute"
