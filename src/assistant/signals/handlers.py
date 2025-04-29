from django.dispatch import receiver

from assistant.models import AssistantProxy
from assistant.signals.signals import assistant_pre_soft_delete, assistant_post_soft_delete


@receiver(assistant_pre_soft_delete, sender=AssistantProxy)
def handle_assistant_pre_soft_delete(sender, instance, **kwargs):
    """
    Handle actions before a Assistant is soft-deleted.
    """
    print(f"Pre soft delete triggered for Assistant: {instance}")


@receiver(assistant_post_soft_delete, sender=AssistantProxy)
def handle_assistant_post_soft_delete(sender, instance, **kwargs):
    """
    Handle actions after a Assistant is soft-deleted.
    """
    print(f"Post soft delete completed for Assistant: {instance}")
