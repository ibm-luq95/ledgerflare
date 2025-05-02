# # signals.py
#
# from django.db.models.signals import pre_save, post_save
# from django.db.transaction import atomic
# from django.dispatch import receiver
# from django.contrib.auth import get_user_model
# import logging
#
# from beach_wood_user.models import BWUser
# from core.utils.developments.debugging_print_object import DebuggingPrint
#
# logger = logging.getLogger(__name__)
#
#
# @receiver(pre_save, sender=BWUser)
# def handle_pre_save(sender, instance: BWUser, **kwargs):
#     """
#     Detects soft deletion before saving the instance.
#     Sets `_is_soft_deleted` flag if `is_deleted` is transitioning to True.
#     """
#     try:
#         if not instance.pk:
#             return  # Skip new instances
#
#         with atomic():
#             try:
#                 original = BWUser.original_objects.filter(pk=instance.pk)
#                 DebuggingPrint.log(original)
#             except BWUser.DoesNotExist:
#                 DebuggingPrint.print_exception(is_show_locales=True)
#                 logger.warning(f"Original user with PK={instance.pk} not found. It may have been hard-deleted.")
#                 return  # Instance may be hard-deleted
#
#             # Detect if this is a soft deletion: is_deleted is changing from False to True
#             if not original.is_deleted and instance.is_deleted:
#                 instance._is_soft_deleted = True
#                 logger.info(
#                     f"Soft deletion detected for user '{instance.email}'. Pre-save logic triggered."
#                 )
#                 # You can add any pre-soft-delete logic here (e.g., revoke tokens, log action)
#     except Exception:
#         DebuggingPrint.print_exception(is_show_locales=True)
#         raise
#
#
# @receiver(post_save, sender=BWUser)
# def handle_post_save(sender, instance: BWUser, created: bool, **kwargs):
#     """
#     Executes cleanup logic only if `_is_soft_deleted` is set.
#     Ensures logic runs only on soft deletions, not on normal updates.
#     """
#     try:
#         if created:
#             return  # Skip if it's a new user
#
#         with atomic():
#             if getattr(instance, "_is_soft_deleted", False):
#                 logger.info(
#                     f"User '{instance.email}' has been soft-deleted. Running post-delete logic."
#                 )
#                 # Perform cleanup tasks here (e.g., delete related data, notify admin)
#
#                 # Clean up the flag to avoid side effects in future saves
#                 del instance._is_soft_deleted
#     except Exception:
#         DebuggingPrint.print_exception(is_show_locales=True)
#         raise
