# -*- coding: utf-8 -*-#
from __future__ import annotations

from django.db.models import QuerySet

from bookkeeper.models import BookkeeperProxy
from cfo.models import CFOProxy
from core.choices import BeachWoodUserTypeEnum


class RoleScopedQuerysetMixin:
    """
    Mixin to scope Django REST Framework ViewSet querysets based on requesting user role.
    Managers and Assistants see everything.
    Bookkeepers and CFOs see only their assigned records.
    """

    def get_queryset(self) -> QuerySet:
        # Start with the default queryset defined on the viewset
        queryset = super().get_queryset()
        user = self.request.user

        if not user or user.is_anonymous:
            return queryset.none()

        user_type = getattr(user, "user_type", None)

        # Superusers, Managers and Assistants have global visibility
        if user.is_superuser or user_type in (
            BeachWoodUserTypeEnum.MANAGER,
            BeachWoodUserTypeEnum.ASSISTANT,
        ):
            return queryset

        # Bookkeepers see assigned items
        elif user_type == BeachWoodUserTypeEnum.BOOKKEEPER:
            try:
                bookkeeper = BookkeeperProxy.objects.get(user=user)
                return self.scope_queryset_for_bookkeeper(queryset, bookkeeper)
            except BookkeeperProxy.DoesNotExist:
                return queryset.none()

        # CFOs see assigned items
        elif user_type == BeachWoodUserTypeEnum.CFO:
            try:
                cfo = CFOProxy.objects.get(user=user)
                return self.scope_queryset_for_cfo(queryset, cfo)
            except CFOProxy.DoesNotExist:
                return queryset.none()

        # Default fallback
        return queryset.none()

    def scope_queryset_for_bookkeeper(self, queryset: QuerySet, bookkeeper: BookkeeperProxy) -> QuerySet:
        """
        Subclasses must override this to filter the queryset for a Bookkeeper.
        """
        return queryset.none()

    def scope_queryset_for_cfo(self, queryset: QuerySet, cfo: CFOProxy) -> QuerySet:
        """
        Subclasses must override this to filter the queryset for a CFO.
        """
        return queryset.none()
