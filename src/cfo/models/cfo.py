from core.models.mixins import BaseModelMixin, StaffMemberMixin
from core.models.mixins.access_proxy_models_mixin import AccessProxyModelMixin


class CFO(BaseModelMixin, StaffMemberMixin, AccessProxyModelMixin):
    """CFO model

    Represents a CFO in the application.
    Inherits from BaseModelMixin, StaffMemberMixin, and AccessProxyModelMixin.
    Meta class defines permissions for the CFO user.
    """

    def natural_key(self) -> tuple[str]:
        """
        Return the natural key of the related BWUser for consistent serialization.

        This ensures that relationships are preserved across fixtures and environments,
        even if UUIDs change.

        Returns
        -------
        tuple[str]
            A single-element tuple containing the email of the associated user.
        """
        return self.user.natural_key()

    natural_key.dependencies = ["beach_wood_user.bwuser"]

    class Meta(BaseModelMixin.Meta, StaffMemberMixin.Meta):
        permissions = [
            ("cfo_user", "CFO User"),
        ]
