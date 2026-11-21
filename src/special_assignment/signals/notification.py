"""
Signals module for handling user messages and creating notifications.
"""

from __future__ import annotations

import textwrap

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext as _

from beach_wood_user.models import BWUser
from core.utils.developments.debugging_print_object import DebuggingPrint
from special_assignment.models import (
    SpecialAssignmentProxy,
    SpecialAssignmentNotification,
)
from lf_notifications.services import NotificationService
from lf_notifications.models import NotificationVerb


@receiver(post_save, sender=SpecialAssignmentProxy)
def create_notification(
    sender: type[SpecialAssignmentProxy],
    instance: SpecialAssignmentProxy,
    created: bool,
    **kwargs,
) -> None:
    """
    Signal receiver that handles post-save events for SpecialAssignmentProxy instances.

    This function is triggered after a SpecialAssignmentProxy instance is saved. It creates
    notifications when new instances are created or updated, depending on the conditions set in the code.

    Parameters
    ----------
    sender : type[SpecialAssignmentProxy]
        The model class (SpecialAssignmentProxy) that emitted the signal.
    instance : SpecialAssignmentProxy
        The instance of SpecialAssignmentProxy that was saved.
    created : bool
        A boolean indicating whether this is a new instance (True) or an update (False).
    kwargs : dict
        Additional keyword arguments passed with the signal.

    Returns
    -------
    None
        This function does not return any value.

    Examples
    --------
    When a new SpecialAssignmentProxy instance is created, `created` will be True:

    >>> # Example of creating a SpecialAssignmentProxy instance
    >>> special_assignment = SpecialAssignmentProxy.objects.create(...)
    >>> # The create_notification function will be triggered with created=True

    When an existing SpecialAssignmentProxy instance is updated, `created` will be False:

    >>> # Example of updating a SpecialAssignmentProxy instance
    >>> special_assignment = SpecialAssignmentProxy.objects.get(...)
    >>> special_assignment.some_field = "new_value"
    >>> special_assignment.save()
    >>> # The create_notification function will be triggered with created=False

    Additional Notes:
    - The try-except block in this function catches any exceptions that may occur during the notification creation process.
    - For production use, consider adding more robust logging or error handling instead of print statements.
    """

    try:
        if created is True:
            special_assignment: SpecialAssignmentProxy = instance
            managed_by: BWUser | None = special_assignment.assigned_to
            if managed_by is not None:
                short_title = textwrap.shorten(
                    special_assignment.title, width=20, placeholder="..."
                )
                data = {
                    "special_assignment": special_assignment,
                    "recipient": managed_by,
                    "msg": f"You assigned a new special assignment {short_title}",
                }
                notification_obj: SpecialAssignmentNotification = (
                    SpecialAssignmentNotification.objects.create(**data)
                )
                NotificationService.trigger(
                    notification_type_name="assignment_assigned",
                    actor=special_assignment.assigned_by,
                    recipients=[managed_by],
                    verb=NotificationVerb.ASSIGNED,
                    context={
                        "actor_name": special_assignment.assigned_by.fullname
                        if special_assignment.assigned_by
                        else _("System"),
                        "assignment_title": special_assignment.title,
                        "url": special_assignment.get_absolute_url(),
                    },
                    content_object=instance,
                )
                # DebuggingPrint.pprint(locals())

    except Exception as e:
        print(f"Error creating notification: {e}")
