# -*- coding: utf-8 -*-#
from rest_framework import serializers

from beach_wood_user.models import BWUser
from discussion.models import DiscussionProxy
from job.models import JobProxy
from special_assignment.models import SpecialAssignment


class DiscussionSerializer(serializers.ModelSerializer):
    special_assignment = serializers.PrimaryKeyRelatedField(
        queryset=SpecialAssignment.original_objects.all(), many=False, required=False
    )
    replies = serializers.PrimaryKeyRelatedField(
        queryset=DiscussionProxy.original_objects.all(), many=False, required=False
    )
    job = serializers.PrimaryKeyRelatedField(
        queryset=JobProxy.original_objects.all(), many=False, required=False
    )
    sender = serializers.PrimaryKeyRelatedField(
        queryset=BWUser.original_objects.all(), many=False, required=False
    )

    class Meta:
        model = DiscussionProxy
        exclude = ("metadata", "is_deleted")
        # depth = 1
