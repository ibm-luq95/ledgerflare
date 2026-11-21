# -*- coding: utf-8 -*-#
from __future__ import annotations

from rest_framework import serializers

from beach_wood_user.models import BWUser
from core.utils.html_sanitizer import sanitize_html
from discussion.models import DiscussionProxy
from job.models import JobProxy
from special_assignment.models import SpecialAssignmentProxy


class DiscussionSerializer(serializers.ModelSerializer):
    special_assignment = serializers.PrimaryKeyRelatedField(
        queryset=SpecialAssignmentProxy.objects.all(), many=False, required=False, allow_null=True
    )
    replies = serializers.PrimaryKeyRelatedField(
        queryset=DiscussionProxy.objects.all(), many=False, required=False, allow_null=True
    )
    job = serializers.PrimaryKeyRelatedField(
        queryset=JobProxy.objects.all(), many=False, required=False, allow_null=True
    )
    sender = serializers.PrimaryKeyRelatedField(
        queryset=BWUser.objects.all(), many=False, required=False, allow_null=True
    )
    sender_name = serializers.SerializerMethodField()
    sender_user_type = serializers.SerializerMethodField()
    sender_avatar = serializers.SerializerMethodField()
    attachment_url = serializers.SerializerMethodField()
    attachment_name = serializers.SerializerMethodField()

    class Meta:
        model = DiscussionProxy
        exclude = ("metadata", "is_deleted")

    def get_sender_name(self, obj: DiscussionProxy) -> str:
        if obj.sender:
            return obj.sender.fullname or obj.sender.get_full_name() or obj.sender.username
        managed_user = obj.get_managed_user()
        return str(managed_user) if managed_user else "Team Member"

    def get_sender_user_type(self, obj: DiscussionProxy) -> str:
        if obj.sender and obj.sender.user_type:
            return str(obj.sender.user_type)
        managed_user = obj.get_managed_user()
        if managed_user and hasattr(managed_user, "user") and managed_user.user:
            return str(managed_user.user.user_type)
        return ""

    def get_sender_avatar(self, obj: DiscussionProxy) -> str:
        managed_user = obj.get_managed_user()
        if (
            managed_user
            and hasattr(managed_user, "profile")
            and managed_user.profile
            and managed_user.profile.profile_picture
        ):
            return managed_user.profile.profile_picture.url
        sender_user = obj.sender
        if sender_user and hasattr(sender_user, "get_staff_member_object"):
            staff_dict = sender_user.get_staff_member_object
            if isinstance(staff_dict, dict):
                staff_obj = staff_dict.get("staff_object")
                if (
                    staff_obj
                    and hasattr(staff_obj, "profile")
                    and staff_obj.profile
                    and staff_obj.profile.profile_picture
                ):
                    return staff_obj.profile.profile_picture.url
        return "/static/img/default_staff.png"

    def get_attachment_url(self, obj: DiscussionProxy) -> str | None:
        if obj.attachment:
            return obj.attachment.url
        return None

    def get_attachment_name(self, obj: DiscussionProxy) -> str | None:
        if obj.attachment:
            return obj.attachment.name.split("/")[-1]
        return None
