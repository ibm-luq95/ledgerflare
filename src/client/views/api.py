# -*- coding: utf-8 -*-#
from django.db import transaction
from django.http import HttpRequest
from django.utils.translation import gettext as _

from rest_framework import permissions, parsers, status
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import APIException

from bookkeeper.models import BookkeeperProxy
from cfo.models import CFOProxy
from client.models import ClientProxy
from client.serializers import ClientSerializer
from core.api.permissions import BaseApiPermissionMixin
from core.utils import get_formatted_logger

logger = get_formatted_logger()


class ClientViewSet(ModelViewSet):
    serializer_class = ClientSerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    parser_classes = [parsers.FormParser, parsers.MultiPartParser]
    perm_slug = "client.client"
    queryset = ClientProxy.objects.all()
    http_method_names = ["post", "patch"]

    @action(
        methods=["POST"],
        detail=False,
        url_path="assign_bookkeeper",
        parser_classes=[parsers.JSONParser],
    )
    def assign_bookkeeper(self, request: HttpRequest, pk=None, *args, **kwargs):
        try:
            data = {}
            client_pk: str = request.data.get("client")
            bookkeeper_pks: list[str] = request.data.get("bookkeepers")
            with transaction.atomic():
                if not client_pk:
                    raise APIException(_("Client is required!"))
                # if not bookkeeper_pks:
                #     raise APIException("Bookkeepers is required!")
                client_obj = ClientProxy.objects.get(pk=client_pk)
                bookkeepers_obj = list(
                    BookkeeperProxy.objects.filter(pk__in=bookkeeper_pks)
                )
                client_obj.bookkeepers.clear()
                client_obj.bookkeepers.add(*bookkeepers_obj)
                client_obj.save()
                data["client_name"] = client_obj.name
                data["bookkeepers"] = ", ".join(
                    [bk.user.fullname for bk in bookkeepers_obj]
                )
                if bookkeeper_pks:
                    data["success_msg"] = _(
                        f"Bookkeepers {data['bookkeepers']} assigned to client {data['client_name']} successfully"
                    )
                else:
                    data["success_msg"] = _(
                        "Bookkeeper(s) removed from client successfully"
                    )
                return Response(
                    data=data, status=status.HTTP_200_OK, content_type="application/json"
                )
        except Exception as ex:
            return Response(
                data={"error": str(ex)},
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/json",
            )

    @action(
        methods=["POST"],
        detail=False,
        url_path="assign_cfos",
        parser_classes=[parsers.JSONParser],
    )
    def assign_cfo(self, request: HttpRequest, pk=None, *args, **kwargs):
        try:
            data = {}
            client_pk: str = request.data.get("client")
            cof_pks: list[str] = request.data.get("cfos")
            with transaction.atomic():
                if not client_pk:
                    raise APIException(_("Client is required!"))
                # if not cof_pks:
                #     raise APIException("Bookkeepers is required!")
                client_obj = ClientProxy.objects.get(pk=client_pk)
                cfos_objects = list(CFOProxy.objects.filter(pk__in=cof_pks))
                client_obj.cfos.clear()
                client_obj.cfos.add(*cfos_objects)
                client_obj.save()
                data["client_name"] = client_obj.name
                data["cfos"] = ", ".join([bk.user.fullname for bk in cfos_objects])
                if cof_pks:
                    data["success_msg"] = _(
                        f"CFO(s) {data['cfos']} assigned to client {data['client_name']} successfully"
                    )
                else:
                    data["success_msg"] = _("CFO(s) removed from client successfully")
                return Response(
                    data=data, status=status.HTTP_200_OK, content_type="application/json"
                )
        except Exception as ex:
            return Response(
                data={"error": str(ex)},
                status=status.HTTP_400_BAD_REQUEST,
                content_type="application/json",
            )
