# -*- coding: utf-8 -*-#
from rest_framework import serializers

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from job.models import JobProxy
from special_assignment.models import SpecialAssignmentProxy


class SpecialAssignmentSerializer(serializers.ModelSerializer):
    assigned_by = serializers.PrimaryKeyRelatedField(
        default=serializers.CurrentUserDefault(), queryset=BWUser.objects.all()
    )
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=BWUser.objects.all())
    job = serializers.PrimaryKeyRelatedField(
        queryset=JobProxy.objects.all(),
        required=False,
        allow_null=True,
    )
    client = serializers.PrimaryKeyRelatedField(
        queryset=ClientProxy.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = SpecialAssignmentProxy
        exclude = ("metadata", "is_deleted", "deleted_at")
        # fields = ("title", "body", "attachment", "assigned_by")
        # read_only_fields = ("assigned_by",)
        # depth = 1
