from django.core.cache import cache
from django.db import transaction
from django.http import HttpRequest
from django.utils.translation import gettext as _
from rest_framework import parsers, permissions, status
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from bookkeeper.models import BookkeeperProxy
from cfo.models import CFOProxy
from client.models import ClientProxy
from client.serializers import ClientDropdownSerializer, ClientSerializer
from core.api.mixins import RoleScopedQuerysetMixin
from core.api.permissions import BaseApiPermissionMixin
from core.constants.users import CON_ASSISTANT, CON_BOOKKEEPER, CON_CFO, CON_MANAGER
from core.utils import get_formatted_logger


logger = get_formatted_logger()


class ClientViewSet(RoleScopedQuerysetMixin, ModelViewSet):
    serializer_class = ClientSerializer
    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    parser_classes = [parsers.JSONParser, parsers.FormParser, parsers.MultiPartParser]
    perm_slug = "client.client"
    queryset = ClientProxy.objects.all()
    http_method_names = ["get", "post", "patch"]
    filterset_fields = ["status", "is_deleted"]
    search_fields = ["name", "email", "phone_number"]
    ordering_fields = ["created_at", "name", "status"]
    ordering = ["name"]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related("bookkeepers", "cfos", "categories")

    def scope_queryset_for_bookkeeper(self, queryset, bookkeeper):
        return queryset.filter(bookkeepers=bookkeeper)

    def scope_queryset_for_cfo(self, queryset, cfo):
        return queryset.filter(cfos=cfo)

    @action(
        methods=["GET"],
        detail=False,
        url_path="search",
        parser_classes=[parsers.JSONParser],
    )
    def search(self, request: HttpRequest, pk=None, *args, **kwargs):
        """
        Search for clients by name. Will return id, name, and dashboard url.
        query parameter 'q' is used.
        """
        q = request.query_params.get("q", "")
        if not q or len(q) < 1:
            return Response([])

        # Scoped queryset based on user role to prevent unauthorized access
        scoped_queryset = self.get_scoped_queryset(request)
        clients = scoped_queryset.filter(name__icontains=q)[:20]
        data = []
        for client in clients:
            data.append({
                "id": str(client.pk),
                "name": client.name,
                "url": client.get_absolute_url()
            })

        return Response(data=data, status=status.HTTP_200_OK)

    def get_scoped_queryset(self, request):
        """
        Get queryset filtered by user role.
        """
        return self.get_queryset()

    @action(
        methods=["POST"],
        detail=False,
        url_path="assign_bookkeeper",
        parser_classes=[parsers.JSONParser],
    )
    def assign_bookkeeper(self, request: HttpRequest, pk=None, *args, **kwargs):
        if not (
            request.user.is_superuser
            or request.user.user_type in (CON_MANAGER, CON_ASSISTANT)
        ):
            return Response(
                data={"error": _("You do not have permission to assign staff.")},
                status=status.HTTP_403_FORBIDDEN,
                content_type="application/json",
            )
        try:
            data = {}
            client_pk: str = request.data.get("client")
            bookkeeper_pks: list[str] = request.data.get("bookkeepers")
            with transaction.atomic():
                if not client_pk:
                    raise APIException(_("Client is required!"))
                client_obj = ClientProxy.objects.get(pk=client_pk)

                # Fetch affected bookkeepers before and after to clear their caches
                old_user_pks = list(client_obj.bookkeepers.values_list("user__pk", flat=True))

                bookkeepers_obj = list(
                    BookkeeperProxy.objects.filter(pk__in=bookkeeper_pks)
                )
                client_obj.bookkeepers.clear()
                client_obj.bookkeepers.add(*bookkeepers_obj)
                client_obj.save()

                # Invalidate user-specific dropdown caches
                new_user_pks = [bk.user.pk for bk in bookkeepers_obj]
                for user_pk in set(old_user_pks + new_user_pks):
                    cache.delete(f"client_dropdown_{user_pk}")

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
        if not (
            request.user.is_superuser
            or request.user.user_type in (CON_MANAGER, CON_ASSISTANT)
        ):
            return Response(
                data={"error": _("You do not have permission to assign staff.")},
                status=status.HTTP_403_FORBIDDEN,
                content_type="application/json",
            )
        try:
            data = {}
            client_pk: str = request.data.get("client")
            cof_pks: list[str] = request.data.get("cfos")
            with transaction.atomic():
                if not client_pk:
                    raise APIException(_("Client is required!"))
                client_obj = ClientProxy.objects.get(pk=client_pk)

                # Fetch affected CFOs before and after to clear their caches
                old_user_pks = list(client_obj.cfos.values_list("user__pk", flat=True))

                cfos_objects = list(CFOProxy.objects.filter(pk__in=cof_pks))
                client_obj.cfos.clear()
                client_obj.cfos.add(*cfos_objects)
                client_obj.save()

                # Invalidate user-specific dropdown caches
                new_user_pks = [cfo.user.pk for cfo in cfos_objects]
                for user_pk in set(old_user_pks + new_user_pks):
                    cache.delete(f"client_dropdown_{user_pk}")

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


class ClientDropdownView(APIView):
    """
    API endpoint for client selector dropdown.
    Returns all clients for managers/assistants, assigned clients for bookkeepers/CFOs.
    Cached per-user for 10 minutes.
    """

    permission_classes = (permissions.IsAuthenticated, BaseApiPermissionMixin)
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    perm_slug = "client.client"

    CACHE_TIMEOUT = 600  # 10 minutes

    def get_queryset(self, request):
        """
        Filter clients based on user type:
        - Superuser/Manager/Assistant: All clients
        - Bookkeeper: Only assigned clients
        - CFO: Only assigned clients
        """
        user = request.user
        user_type = getattr(user, "user_type", None)

        # Superuser, Manager or Assistant: All clients
        if user.is_superuser or user_type in (CON_MANAGER, CON_ASSISTANT):
            return ClientProxy.objects.all()

        # Bookkeeper: Only assigned clients
        if user_type == CON_BOOKKEEPER:
            try:
                bookkeeper = BookkeeperProxy.objects.get(user=user)
                return ClientProxy.objects.filter(bookkeepers=bookkeeper)
            except BookkeeperProxy.DoesNotExist:
                return ClientProxy.objects.none()

        # CFO: Only assigned clients
        elif user_type == CON_CFO:
            try:
                cfo = CFOProxy.objects.get(user=user)
                return ClientProxy.objects.filter(cfos=cfo)
            except CFOProxy.DoesNotExist:
                return ClientProxy.objects.none()

        # Default: No clients
        return ClientProxy.objects.none()

    def get(self, request: HttpRequest, *args, **kwargs):
        # Cache per-user to prevent cross-user data leakage
        cache_key = f"client_dropdown_{request.user.pk}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data, status=status.HTTP_200_OK)

        # Fetch from database
        queryset = self.get_queryset(request)
        serializer = ClientDropdownSerializer(
            queryset,
            many=True,
            context={"request": request}
        )

        # Cache the result
        cache.set(cache_key, serializer.data, timeout=self.CACHE_TIMEOUT)

        return Response(serializer.data, status=status.HTTP_200_OK)
