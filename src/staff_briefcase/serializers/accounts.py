# -*- coding: utf-8 -*-#
import traceback

from django.db import transaction
from rest_framework import serializers

from core.choices import ServiceNameEnum
from staff_briefcase.models import StaffAccounts, StaffBriefcase


class StaffAccountsSerializer(serializers.ModelSerializer):
    briefcase = serializers.UUIDField(required=True, write_only=True)
    has_password = serializers.SerializerMethodField()
    name = serializers.ChoiceField(
        choices=ServiceNameEnum.choices,
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    url = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    username_email = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    password = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        write_only=True,
    )

    class Meta:
        model = StaffAccounts
        fields = (
            "id",
            "title",
            "url",
            "briefcase",
            "username_email",
            "password",
            "has_password",
            "name",
        )
        depth = 1

    def get_has_password(self, obj: StaffAccounts) -> bool:
        return bool(obj.password)

    def create(self, validated_data):
        try:
            with transaction.atomic():
                briefcase_pk = validated_data.pop("briefcase")
                briefcase_obj = StaffBriefcase.objects.get(pk=briefcase_pk)
                obj = StaffAccounts.objects.create(**validated_data)
                briefcase_obj.accounts.add(obj)
                briefcase_obj.save()
                # obj.save(foo=validated_data["foo"])
                return obj
        except Exception as ex:
            print(traceback.format_exc())
