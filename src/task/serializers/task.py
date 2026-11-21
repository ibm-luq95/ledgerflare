# -*- coding: utf-8 -*-#
from django.utils import timezone
from rest_framework import serializers

from job.models import JobProxy
from task.models import TaskProxy


class TaskSerializer(serializers.ModelSerializer):
    # task_type_display = serializers.CharField(
    #     source="get_task_type_display", required=False
    # )
    # status_display = serializers.CharField(
    #     source="get_status_display", required=False
    # )
    job = serializers.PrimaryKeyRelatedField(
        queryset=JobProxy.objects.all(), many=False
    )

    class Meta:
        model = TaskProxy
        # fields = ("get_task_type_display",)
        exclude = (
            "metadata",
            "is_deleted",
            # "user",
            "deleted_at",
            "updated_at",
            "is_completed",
        )
        depth = 2
