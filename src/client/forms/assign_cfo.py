from typing import Optional

from bookkeeper.models import BookkeeperProxy
from cfo.models import CFOProxy
from client.models import ClientProxy
from core.forms.mixins.base_form_mixin import BWBaseFormMixin
from django import forms


class AssignCFOForm(BWBaseFormMixin):
    def __init__(self, client: Optional[ClientProxy] = None, *args, **kwargs):
        super(BWBaseFormMixin, self).__init__(*args, **kwargs)
        if client is not None:
            client_cfos = client.cfos.all()
            self.fields.get("cfos").initial = client_cfos

    cfos = forms.ModelMultipleChoiceField(
        queryset=CFOProxy.objects.all(),
        widget=forms.CheckboxSelectMultiple,
    )
