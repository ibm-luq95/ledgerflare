# -*- coding: utf-8 -*-#
from core.models.mixins import StaffMemberMixin, BaseModelMixin
from core.models.mixins.access_proxy_models_mixin import AccessProxyModelMixin


class Manager(BaseModelMixin, StaffMemberMixin, AccessProxyModelMixin):
    """Manager model represents the manager of the app

    Args:
        CustomUser (User): Django custom user model
    """

    # def natural_key(self) -> tuple[str]:
    #     """
    #     Return the natural key of the related BWUser for consistent serialization.
    #
    #     This ensures that relationships are preserved across fixtures and environments,
    #     even if UUIDs change.
    #
    #     Returns
    #     -------
    #     tuple[str]
    #         A single-element tuple containing the email of the associated user.
    #     """
    #     return self.user.natural_key()
    #
    # natural_key.dependencies = ["beach_wood_user.bwuser"]

    class Meta(BaseModelMixin.Meta, StaffMemberMixin.Meta):
        permissions = [("manager_user", "Manager User")]
