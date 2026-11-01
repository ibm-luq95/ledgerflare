# -*- coding: utf-8 -*-#
import traceback

from django.db import transaction
from rest_framework import serializers

from staff_briefcase.models import StaffBriefcase, StaffDocuments


class StaffDocumentsSerializer(serializers.ModelSerializer):
    briefcase = serializers.UUIDField(required=True, write_only=True)

    def validate_document_file(self, value):
        from core.constants.file_types_validation import IMAGES_AND_DOCS_FT
        from core.utils import FileValidator
        validator = FileValidator(max_size=1024 * 1024 * 100, content_types=IMAGES_AND_DOCS_FT)
        validator(value)
        return value

    class Meta:
        model = StaffDocuments
        fields = ("id", "title", "document_file", "briefcase")
        depth = 1

    def create(self, validated_data):
        try:
            with transaction.atomic():
                briefcase_pk = validated_data.pop("briefcase")
                briefcase_obj = StaffBriefcase.objects.get(pk=briefcase_pk)
                obj = StaffDocuments.objects.create(**validated_data)
                briefcase_obj.documents.add(obj)
                briefcase_obj.save()
                # obj.save(foo=validated_data["foo"])
                return obj
        except Exception as ex:
            print(traceback.format_exc())
