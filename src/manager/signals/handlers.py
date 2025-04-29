from django.dispatch import receiver

from manager.models import ManagerProxy
from manager.signals.signals import manager_pre_soft_delete, manager_post_soft_delete


@receiver(manager_pre_soft_delete, sender=ManagerProxy)
def handle_manager_pre_soft_delete(sender, instance, **kwargs):
    """
    Handle actions before a Manager is soft-deleted.
    """
    print(f"Pre soft delete triggered for Manager: {instance}")


@receiver(manager_post_soft_delete, sender=ManagerProxy)
def handle_manager_post_soft_delete(sender, instance, **kwargs):
    """
    Handle actions after a Manager is soft-deleted.
    """
    print(f"Post soft delete completed for Manager: {instance}")
