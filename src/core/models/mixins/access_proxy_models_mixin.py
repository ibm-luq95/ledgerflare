from typing import Optional

from django.db import models
from django.db.models import Model


class AccessProxyModelMixin(models.Model):
    """Abstract base class that provides a method to retrieve the proxy model for a given
    instance.

    This class is meant to be used as a mixin for other models that have corresponding proxy models.
    The `get_proxy_model` method retrieves the appropriate proxy model based on the model name.

    Attributes:
        None

    Methods:
        get_proxy_model(): Retrieves the proxy model for the current instance.

    Meta:
        abstract = True: This class is meant to be used as a base class and cannot be instantiated on its own.

    """

    class Meta:
        abstract = True

    def get_proxy_model(self) -> Optional[Model]:
        """Retrieves the proxy model for the current instance.

        This method checks the model name of the current instance and retrieves the corresponding proxy model.
        The proxy models are imported dynamically based on the model name.

        Returns:
            The proxy model for the current instance, or None if no proxy model is found.

        """
        model = None
        model_name = self._meta.verbose_name
        match model_name:
            case "bookkeeper":
                from bookkeeper.models.bookkeeper_proxy import BookkeeperProxy

                model = BookkeeperProxy.objects.get(pk=self.pk)
            case "manager":
                from manager.models.manager_proxy import ManagerProxy

                model = ManagerProxy.objects.get(pk=self.pk)
            case "assistant":
                from assistant.models.assistant_proxy import AssistantProxy

                model = AssistantProxy.objects.get(pk=self.pk)
            case "cfo":
                from cfo.models.proxy import CFOProxy

                model = CFOProxy.objects.get(pk=self.pk)
            case "job":
                from job.models.job_proxy import JobProxy

                model = JobProxy.objects.get(pk=self.pk)
            case "client":
                from client.models.client_proxy import ClientProxy

                model = ClientProxy.objects.get(pk=self.pk)
            case "task":
                from task.models.proxy_model import TaskProxy

                model = TaskProxy.objects.get(pk=self.pk)
        return model
