from rest_framework import serializers

from job.models import JobProxy
from note.models import Note


class NoteSerializer(serializers.ModelSerializer):
    job = serializers.PrimaryKeyRelatedField(
        queryset=JobProxy.objects.all(), many=False, required=False
    )

    class Meta:
        model = Note
        exclude = (
            "metadata",
            "is_deleted",
            # "created_at",
            "updated_at",
            "deleted_at",
        )
        # depth = 1
