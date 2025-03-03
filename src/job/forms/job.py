from typing import Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django import forms

from django.utils.safestring import mark_safe

from beach_wood_user.models import BWUser
from client.models import ClientProxy
from core.forms import BaseModelFormMixin, JoditFormMixin
from core.forms.mixins.js_modal_form_renderer_mixin import BWJSModalFormRendererMixin
from core.forms.widgets import RichHTMLEditorWidget
from job.models import JobProxy


class JobForm(BWJSModalFormRendererMixin, BaseModelFormMixin, JoditFormMixin):
    field_order = [
        "title",
        "client",
        "managed_by",
        "start_date",
        # "is_scheduled",
        "due_date",
        "period_year",
        "period_month",
        "description",
        "status",
        "job_type",
        "note",
    ]

    def __init__(
        self,
        user: Optional[BWUser] = None,
        client=None,
        user_type: Optional[str] = None,
        is_updated=False,
        add_jodit_css_class=False,
        *args,
        **kwargs,
    ):
        super(JobForm, self).__init__(*args, **kwargs)
        JoditFormMixin.__init__(self, add_jodit_css_class=add_jodit_css_class)
        self.user_type = user_type
        self.user = user
        self.is_update = is_updated
        # self.fields["start_date"].initial = None
        if client is not None:
            self.fields["client"].initial = client
        else:
            self.fields["client"].queryset = ClientProxy.objects.all().order_by("name")

        self.fields["managed_by"].queryset = BWUser.objects.all().order_by("first_name")
        if self.initial.get("client", None) is not None:
            if hasattr(self.instance.client, "bookkeepers"):
                all_client_bookkeepers = self.instance.client.bookkeepers.all()
                # debugging_print(all_client_bookkeepers)
                bookkeepers_pks = [
                    bookkeeper.user.pk for bookkeeper in all_client_bookkeepers
                ]
                self.fields["managed_by"].queryset = BWUser.objects.filter(
                    pk__in=bookkeepers_pks
                ).order_by("first_name")
                self.fields["managed_by"].help_text = mark_safe(
                    "<strong>Bookkeepers who assigned for this client</strong>"
                )
        if self.user_type is not None:
            if self.user_type == "bookkeeper":
                self.fields["managed_by"].widget = forms.HiddenInput()
                self.fields["managed_by"].initial = self.user.pk

    # def clean_due_date(self):
    #     data = self.cleaned_data["due_date"]
    #     now = timezone.now().date()
    #
    #     if self.is_update is False:
    #         if data < now:
    #             raise ValidationError(_("Due date not valid!"), code="invalid")
    #
    #     # Always return a value to use as the new cleaned data, even if
    #     # this method didn't change it.
    #     return data

    def save(self, commit=True):
        # Save the provided password in hashed format
        try:
            job = super().save(commit=False)
            with transaction.atomic():
                if commit is True:
                    job.save()
                    self.save_m2m()
            return job
        except Exception as e:
            raise ValidationError(str(e))

    class Meta(BaseModelFormMixin.Meta):
        model = JobProxy
        exclude = BaseModelFormMixin.Meta.exclude + ["scheduled_date", "is_scheduled"]
        widgets = {
            "categories": forms.CheckboxSelectMultiple,
            "description": RichHTMLEditorWidget,
            "note": RichHTMLEditorWidget,
        }
