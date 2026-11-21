# -*- coding: utf-8 -*-#
import traceback

from django.db import transaction
from rest_framework import serializers

from staff_briefcase.models import StaffNotes, StaffBriefcase


class StaffNotesSerializer(serializers.ModelSerializer):
    briefcase = serializers.UUIDField(required=True, write_only=True)

    class Meta:
        model = StaffNotes
        fields = ("id", "title", "note", "briefcase")
        depth = 1

    def create(self, validated_data):
        try:
            with transaction.atomic():
                briefcase_pk = validated_data.pop("briefcase")
                briefcase_obj = StaffBriefcase.objects.get(pk=briefcase_pk)
                obj = StaffNotes.objects.create(**validated_data)
                briefcase_obj.notes.add(obj)
                briefcase_obj.save()
                # obj.save(foo=validated_data["foo"])
                return obj
        except Exception as ex:
            print(traceback.format_exc())
