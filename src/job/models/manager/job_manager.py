from core.constants.status_labels import CON_ARCHIVED
from core.constants.status_labels import CON_COMPLETED
from core.models.managers import SoftDeleteManager
from core.models.querysets import BaseQuerySetMixin


class JobManager(SoftDeleteManager):
    def get_queryset(self) -> BaseQuerySetMixin:
        # Only apply universal filters (e.g., soft-delete)
        return super().get_queryset()  # already filters is_deleted=False

    def active(self):
        """Return jobs that are not completed or archived."""
        return self.get_queryset().exclude(status__in=[CON_ARCHIVED, CON_COMPLETED])

    def completed_or_archived(self):
        """Return jobs that are completed or archived."""
        return self.get_queryset().filter(status__in=[CON_ARCHIVED, CON_COMPLETED])

    def all_non_deleted(self):
        return self.get_queryset()  # i.e., is_deleted=False, no status filter
