# -*- coding: utf-8 -*-#
from rest_framework import serializers

from client_account.models import ClientAccount
from core.constants import EXCLUDED_FIELDS


class ClientAccountSerializer(serializers.ModelSerializer):
    has_password = serializers.SerializerMethodField()

    class Meta:
        model = ClientAccount
        exclude = EXCLUDED_FIELDS
        extra_kwargs = {"account_password": {"write_only": True}}

    def get_has_password(self, obj: ClientAccount) -> bool:
        return bool(obj.account_password)
