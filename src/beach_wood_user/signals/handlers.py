from django.dispatch import receiver

from beach_wood_user.models import BWUser
from beach_wood_user.signals.signals import bwuser_pre_soft_delete, bwuser_post_soft_delete


@receiver(bwuser_pre_soft_delete, sender=BWUser)
def handle_bwuser_pre_soft_delete(sender, instance, **kwargs):
    """
    Handle actions before a BWUser is soft-deleted.
    """
    print(f"Pre soft delete triggered for BWUser: {instance}")


@receiver(bwuser_post_soft_delete, sender=BWUser)
def handle_bwuser_post_soft_delete(sender, instance, **kwargs):
    """
    Handle actions after a BWUser is soft-deleted.
    """
    print(f"Post soft delete completed for BWUser: {instance}")
