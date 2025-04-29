# -*- coding: utf-8 -*-#
from __future__ import annotations

from random import randint
from typing import Any

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import Permission
from django.db import transaction, models
from django.db.models import Q, QuerySet, Model
from django.db.models.aggregates import Count
from django.utils.translation import gettext as _

from core.models.querysets import BaseQuerySetMixin
from core.utils.grab_env_file import grab_env_file


class BeachWoodUserManager(BaseUserManager, models.Manager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """

    def get_queryset(self) -> QuerySet[Model | Any, Model | Any]:
        queryset = BaseQuerySetMixin(self.model, using=self._db).filter(is_deleted=False)
        return queryset

    def delete(self):
        """
        Soft delete all objects in the queryset.
        """
        return self.get_queryset().delete()

    def restore(self):
        """
        Restore all soft-deleted objects in the queryset.
        """
        return self.get_queryset().restore()

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        with transaction.atomic():
            if not email:
                raise ValueError(_("The Email must be set"))
            email = self.normalize_email(email)
            user = self.model(email=email, **extra_fields)
            user.set_password(password)
            user.save()
            # if user.user_type == "manager":
            #     Manager.objects.select_for_update().create(user=user)
            return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        with transaction.atomic():
            extra_fields.setdefault("is_staff", True)
            extra_fields.setdefault("is_superuser", True)
            extra_fields.setdefault("is_active", True)
            config = grab_env_file()
            development_admin_emails = ["admin@admin.com", "admin@admin.dev"]

            # create admin names for superuser in case it is admin
            if email in development_admin_emails and (
                config("STAGE_ENVIRONMENT", cast=str) == "DEV"
                or config("STAGE_ENVIRONMENT", cast=str) == "LOCAL_DEV"
            ):
                extra_fields.setdefault("first_name", "Administrator")
                extra_fields.setdefault("last_name", "Account")
                extra_fields.setdefault("user_type", "manager")

            if extra_fields.get("is_staff") is not True:
                raise ValueError(_("Superuser must have is_staff=True."))
            if extra_fields.get("is_superuser") is not True:
                raise ValueError(_("Superuser must have is_superuser=True."))
            created_user = self.create_user(email, password, **extra_fields)
            developer_permission = Permission.objects.get(codename="developer_user")
            created_user.user_permissions.add(developer_permission)
            return created_user

    def random(self):
        count = self.aggregate(count=Count("id"))["count"]
        random_index = randint(0, count - 1)
        return self.all()[random_index]
