from __future__ import annotations

from rest_framework import serializers
from lf_notifications.models import NotificationProxy, NotificationRecipientProxy

class NotificationSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.fullname", read_only=True)
    actor_avatar = serializers.SerializerMethodField()
    content_object_type = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationProxy
        fields = [
            "id", "actor", "actor_name", "actor_avatar", "verb", 
            "message_template", "content_type", "object_id", 
            "content_object_type", "created_at", "metadata"
        ]

    def get_actor_avatar(self, obj: NotificationProxy) -> str | None:
        if obj.actor:
            staff_details = obj.actor.get_staff_details()
            profile_picture = staff_details.get("profile_picture")
            if profile_picture:
                return profile_picture.url
        return None

    def get_content_object_type(self, obj: NotificationProxy) -> str | None:
        if obj.content_type:
            return obj.content_type.model
        return None

class NotificationRecipientSerializer(serializers.ModelSerializer):
    notification = NotificationSerializer(read_only=True)
    
    class Meta:
        model = NotificationRecipientProxy
        fields = ["id", "notification", "is_read", "read_at", "is_seen", "seen_at"]
        read_only_fields = ["read_at", "seen_at"]
