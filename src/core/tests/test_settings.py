# -*- coding: utf-8 -*-#
from __future__ import annotations

import pytest
from django.conf import settings


@pytest.mark.django_db
def test_db_conn_max_age_configured() -> None:
    db_config = settings.DATABASES["default"]
    assert "CONN_MAX_AGE" in db_config
    assert db_config["CONN_MAX_AGE"] >= 60
