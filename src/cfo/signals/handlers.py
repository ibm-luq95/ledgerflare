from django.dispatch import receiver

from cfo.models import CFOProxy
from cfo.signals.signals import cfo_pre_soft_delete, cfo_post_soft_delete


@receiver(cfo_pre_soft_delete, sender=CFOProxy)
def handle_cfo_pre_soft_delete(sender, instance, **kwargs):
    """
    Handle actions before a CFO is soft-deleted.
    """
    print(f"Pre soft delete triggered for CFO: {instance}")


@receiver(cfo_post_soft_delete, sender=CFOProxy)
def handle_cfo_post_soft_delete(sender, instance, **kwargs):
    """
    Handle actions after a CFO is soft-deleted.
    """
    print(f"Post soft delete completed for CFO: {instance}")
