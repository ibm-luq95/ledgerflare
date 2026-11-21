from rest_framework import serializers

from client.models import ClientProxy
from core.constants import EXCLUDED_FIELDS
from important_contact.models import ImportantContact


class ImportantContactSerializer(serializers.ModelSerializer):
    client = serializers.UUIDField()

    class Meta:
        model = ImportantContact
        exclude = EXCLUDED_FIELDS
        # depth = 2

    def create(self, validated_data):
        client = validated_data.pop("client")
        contact = ImportantContact.objects.create(**validated_data)
        if client:
            client_object = ClientProxy.objects.get(pk=client)
            client_object.important_contacts.add(contact)
            client_object.save()
        return contact
