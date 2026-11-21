"""Helper utility for retrieving default BeachWood staff permissions."""
from __future__ import annotations

from typing import Any

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet

from core.constants.users import DEFAULT_PERMISSIONS_NEW_STAFF_MEMBER
from core.models.querysets import BaseQuerySetMixin


class PermissionHelper:
    """Helper class providing utilities for default permission resolution."""

    @classmethod
    def get_bw_default_permissions(
        cls,
        as_list: bool = False,
        as_qs: bool = False,
        as_form_choices: bool = False,
    ) -> list[Permission] | QuerySet[Permission] | list[tuple[int, Permission]]:
        """Retrieve default Django permission instances for new staff members."""
        permissions_codename_list_objs: list[Permission] = []
        for content_type_item in DEFAULT_PERMISSIONS_NEW_STAFF_MEMBER:
            content_type_object = ContentType.objects.get(
                app_label=content_type_item["app_label"],
                model=content_type_item["model_label"],
            )
            permissions_codename_labels = content_type_item.get(
                "permissions_codename_labels", []
            )
            extra_permissions = content_type_item.get("extra_permissions", {})
            extra_permissions_codename_labels = extra_permissions.get(
                "codename_labels", []
            )

            all_codenames = list(permissions_codename_labels)
            if extra_permissions_codename_labels:
                all_codenames.extend(extra_permissions_codename_labels)

            for codename in all_codenames:
                permission_object = Permission.objects.get(
                    codename=codename, content_type=content_type_object
                )
                if permission_object not in permissions_codename_list_objs:
                    permissions_codename_list_objs.append(permission_object)

        if as_qs:
            permissions_pks = [p.pk for p in permissions_codename_list_objs]
            return Permission.objects.filter(pk__in=permissions_pks)
        if as_form_choices:
            return [
                (permission.pk, permission)
                for permission in permissions_codename_list_objs
            ]
        return permissions_codename_list_objs



