from typing import ClassVar

from core.forms import BaseModelFormMixin
from core.forms.mixins.set_bookkeeper_related_mixin import (
    InitBookkeeperRelatedFieldsMixin,
)
from core.forms.widgets import RichHTMLEditorWidget
from task.models import TaskProxy


class TaskForm(BaseModelFormMixin):
    field_order: ClassVar[list] = [
        "title",
        "job",
        "task_type",
        "status",
        "start_date",
        "due_date",
        "additional_notes",
        "hints",
    ]

    def __init__(
        self,
        hidden_fields: list | None = None,
        bookkeeper=None,
        *args,
        **kwargs,
    ):
        super(TaskForm, self).__init__(*args, **kwargs)
        InitBookkeeperRelatedFieldsMixin.__init__(self, bookkeeper=bookkeeper)
        # JoditFormMixin.__init__(self, add_jodit_css_class=add_jodit_css_class)
        # RemoveFieldsMixin.__init__(self, removed_fields=removed_fields)
        self.fields["job"].widget.attrs.update({"class": "js-choice-select"})
        if hidden_fields is not None:
            for field in hidden_fields:
                self.fields.pop(field)

    class Meta(BaseModelFormMixin.Meta):
        model = TaskProxy
        widgets: ClassVar[dict] = {"additional_notes": RichHTMLEditorWidget}
