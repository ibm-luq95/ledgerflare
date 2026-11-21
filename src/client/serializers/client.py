from django.urls import reverse
from rest_framework import serializers

from client.models import ClientProxy


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProxy
        exclude = ("metadata", "is_deleted")
        # depth = 1


class ClientDropdownSerializer(serializers.ModelSerializer):
    """Lightweight serializer for dropdown client selector display"""

    logo_url = serializers.SerializerMethodField()
    dashboard_url = serializers.SerializerMethodField()

    class Meta:
        model = ClientProxy
        fields = ["id", "name", "email", "logo_url", "dashboard_url"]
        read_only_fields = fields

    def get_logo_url(self, obj) -> str | None:
        request = self.context.get("request")
        if obj.company_logo and request:
            return request.build_absolute_uri(obj.company_logo.url)
        return None

    def get_dashboard_url(self, obj) -> str:
        return reverse("dashboard:client:details", kwargs={"pk": obj.pk})
