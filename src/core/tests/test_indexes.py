# -*- coding: utf-8 -*-#
from __future__ import annotations

import pytest
from django.contrib.postgres.indexes import GinIndex
from core.models.mixins.base_model import BaseModelMixin
from job.models import JobProxy
from task.models import TaskProxy


@pytest.mark.django_db
def test_base_model_has_metadata_gin_index() -> None:
    indexes = BaseModelMixin._meta.indexes
    has_gin = any(
        isinstance(idx, GinIndex) and idx.fields == ["metadata"] for idx in indexes
    )
    assert has_gin, "BaseModelMixin must include a GinIndex on metadata"


@pytest.mark.django_db
def test_job_model_has_status_and_is_deleted_indexes() -> None:
    job_fields = {f.name: f for f in JobProxy._meta.get_fields() if hasattr(f, "db_index")}
    assert job_fields["status"].db_index is True
    assert job_fields["is_deleted"].db_index is True


@pytest.mark.django_db
def test_task_model_has_status_and_is_deleted_indexes() -> None:
    task_fields = {f.name: f for f in TaskProxy._meta.get_fields() if hasattr(f, "db_index")}
    assert task_fields["status"].db_index is True
    assert task_fields["is_deleted"].db_index is True
