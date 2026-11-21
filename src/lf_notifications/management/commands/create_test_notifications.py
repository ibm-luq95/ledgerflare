from __future__ import annotations

import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from lf_notifications.services import NotificationService
from lf_notifications.models import NotificationVerb
from job.models import JobProxy
from special_assignment.models import SpecialAssignmentProxy
from discussion.models import DiscussionProxy

User = get_user_model()

class Command(BaseCommand):
    help = "Generates test notifications for the current user or all users."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count", type=int, default=5, help="Number of notifications to create per type"
        )
        parser.add_argument(
            "--email", type=str, help="Specific user email to receive notifications"
        )

    def handle(self, *args, **options):
        count = options["count"]
        email = options["email"]

        if email:
            recipients = User.objects.filter(email=email)
        else:
            recipients = User.objects.filter(is_active=True)[:5]

        if not recipients.exists():
            self.stdout.write(self.style.ERROR("No active users found to receive notifications."))
            return

        actors = User.objects.all()
        jobs = JobProxy.objects.all()
        assignments = SpecialAssignmentProxy.objects.all()
        discussions = DiscussionProxy.objects.all()

        self.stdout.write(self.style.SUCCESS(f"Generating test notifications for {recipients.count()} users..."))

        for recipient in recipients:
            actor = random.choice(actors) if actors.exists() else recipient
            
            # 1. Discussion Created
            job = random.choice(jobs) if jobs.exists() else None
            NotificationService.trigger(
                notification_type_name="discussion_created",
                actor=actor,
                recipients=[recipient],
                verb=NotificationVerb.COMMENTED,
                context={
                    "actor_name": actor.fullname,
                    "target_name": job.title if job else "Test Job",
                    "url": job.get_absolute_url() if job else "/",
                },
                content_object=random.choice(discussions) if discussions.exists() else None
            )

            # 2. Assignment Assigned
            assignment = random.choice(assignments) if assignments.exists() else None
            NotificationService.trigger(
                notification_type_name="assignment_assigned",
                actor=actor,
                recipients=[recipient],
                verb=NotificationVerb.ASSIGNED,
                context={
                    "actor_name": actor.fullname,
                    "assignment_title": assignment.title if assignment else "Test Assignment",
                    "url": assignment.get_absolute_url() if assignment else "/",
                },
                content_object=assignment
            )

            # 3. Job Scheduled
            job = random.choice(jobs) if jobs.exists() else None
            NotificationService.trigger(
                notification_type_name="job_scheduled",
                actor=None,
                recipients=[recipient],
                verb=NotificationVerb.CREATED,
                context={
                    "job_title": job.title if job else "Scheduled Job",
                    "url": job.get_absolute_url() if job else "/",
                },
                content_object=job
            )

        self.stdout.write(self.style.SUCCESS("Successfully created test notifications."))
