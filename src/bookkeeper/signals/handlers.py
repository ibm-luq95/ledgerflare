from django.dispatch import receiver

from bookkeeper.models import BookkeeperProxy
from bookkeeper.signals.signals import (
    bookkeeper_pre_soft_delete,
    bookkeeper_post_soft_delete,
)


@receiver(bookkeeper_pre_soft_delete, sender=BookkeeperProxy)
def handle_bookkeeper_pre_soft_delete(sender, instance, **kwargs):
    """
    Handle actions before a Bookkeeper is soft-deleted.
    """
    print(f"Pre soft delete triggered for Bookkeeper: {instance}")


@receiver(bookkeeper_post_soft_delete, sender=BookkeeperProxy)
def handle_bookkeeper_post_soft_delete(sender, instance, **kwargs):
    """
    Handle actions after a Bookkeeper is soft-deleted.
    """
    print(f"Post soft delete completed for Bookkeeper: {instance}")
