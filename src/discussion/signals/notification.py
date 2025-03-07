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
                short_title = textwrap.shorten(job.title, width=10, placeholder="...")
                managed_by: BWUser = job.managed_by
                discussions_users: list[BWUser] | None = job.get_staff_discussions()
                if discussions_users is not None:
                    DebuggingPrint.pprint("Discussion user")
                    DebuggingPrint.pprint(discussions_users)
                    for discussion_user in discussions_users:
                        if discussion_user != instance.sender:
                            DebuggingPrint.pprint("Not equal")
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
                            DebuggingPrint.pprint("No discussion user")
                            manager_user = BWUser.objects.filter(
                                email=settings.MANAGER_MAIN_EMAIL
                            ).first()
                            DebuggingPrint.pprint(manager_user)
                            notification_obj: DiscussionNotification = (
                                DiscussionNotification(
                                    discussion=instance,
                                    job=job,
                                    recipient=manager_user,
                                    msg=_("You have notification for job ") + short_title,
                                )
                            )
                            notification_obj.save()
                            break
            elif isinstance(instance.for_what(), SpecialAssignmentProxy):
                pass
    except Exception as e:
        print(f"Error creating notification: {e}")
