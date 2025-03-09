"""
Signals module for handling user messages and creating notifications.
"""

from __future__ import annotations

import textwrap

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext as _

from beach_wood_user.models import BWUser
from core.utils.developments.debugging_print_object import DebuggingPrint
from discussion.models import DiscussionProxy, DiscussionNotification
from job.models import JobProxy
from manager.models import ManagerProxy
from special_assignment.models import SpecialAssignmentProxy


@receiver(post_save, sender=DiscussionProxy)
def create_notification(
    sender: type[DiscussionProxy], instance: DiscussionProxy, created: bool, **kwargs
) -> None:
    """
    Signal handler to create a notification when a message is saved.

    Parameters
    ----------
    sender : type[Message]
        The model class.
    instance : Message
        The instance of the model that was saved.
    created : bool
        A boolean indicating whether a new record was created.
    **kwargs
        Additional keyword arguments passed to the signal handler.

    Raises
    ------
    Exception
        If an error occurs during notification creation.
    """

    try:
        if created:
            if isinstance(instance.for_what(), JobProxy):
                job: JobProxy = instance.for_what()
                short_title = textwrap.shorten(job.title, width=20, placeholder="...")
                managed_by: BWUser = job.managed_by
                discussions_users: list[BWUser] | None = job.get_staff_discussions()
                if discussions_users is not None:
                    # DebuggingPrint.pprint("Discussion user")
                    # DebuggingPrint.pprint(discussions_users)
                    for discussion_user in discussions_users:
                        if discussion_user != instance.sender:
                            # DebuggingPrint.pprint("Not equal")
                            notification_obj: DiscussionNotification = (
                                DiscussionNotification(
                                    discussion=instance,
                                    job=job,
                                    recipient=discussion_user,
                                    msg=_("You have notification for job ") + short_title,
                                )
                            )
                            notification_obj.save()
                            break
                        else:
                            # if there is no discussion user, it will send the manager by default
                            # DebuggingPrint.pprint("No discussion user")
                            if managed_by is not None and managed_by != instance.sender:
                                # DebuggingPrint.pprint("Managed by")
                                notification_obj: DiscussionNotification = (
                                    DiscussionNotification(
                                        discussion=instance,
                                        job=job,
                                        recipient=managed_by,
                                        msg=_("You have notification for job ")
                                        + short_title,
                                    )
                                )
                                notification_obj.save()
                                break
                            else:
                                manager_user = BWUser.objects.filter(
                                    email=settings.MANAGER_MAIN_EMAIL
                                ).first()
                                # DebuggingPrint.pprint(manager_user)
                                notification_obj: DiscussionNotification = (
                                    DiscussionNotification(
                                        discussion=instance,
                                        job=job,
                                        recipient=manager_user,
                                        msg=_("You have notification for job ")
                                        + short_title,
                                    )
                                )
                                notification_obj.save()
                                break
            elif isinstance(instance.for_what(), SpecialAssignmentProxy):
                special_assignment: SpecialAssignmentProxy = instance.for_what()
                short_title = textwrap.shorten(
                    special_assignment.title, width=20, placeholder="..."
                )
                managed_by: BWUser = special_assignment.get_managed_user().user
                # DebuggingPrint.pprint(f"Managed by: {managed_by}")
                # DebuggingPrint.pprint(f"Sender : {instance.sender}")

                if instance.sender != managed_by:
                    notification_obj: DiscussionNotification = DiscussionNotification(
                        discussion=instance,
                        special_assignment=special_assignment,
                        recipient=managed_by,
                        msg=_("You have notification for assignment ") + short_title,
                    )
                    notification_obj.save()

                elif instance.sender == managed_by:
                    # DebuggingPrint.pprint("SDFSFD")
                    manager_user = BWUser.objects.filter(
                        email=settings.MANAGER_MAIN_EMAIL
                    ).first()
                    notification_obj: DiscussionNotification = DiscussionNotification(
                        discussion=instance,
                        special_assignment=special_assignment,
                        recipient=manager_user,
                        msg=_("You have notification for assignment ") + short_title,
                    )
                    notification_obj.save()
                # DebuggingPrint.pprint(locals())
    except Exception as e:
        print(f"Error creating notification: {e}")
