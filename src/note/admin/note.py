from django.contrib import admin
from django.utils.html import format_html, mark_safe

from core.admin import BWBaseAdminModelMixin
from note.models import Note


@admin.register(Note)
class NoteAdmin(BWBaseAdminModelMixin):

    list_display = [
        "title",
        "note_section",
        "status",
        "client",
        "job",
        "task",
        "get_multiple_sections",
        "created_at",
    ]
    list_filter = ["note_section", "status", "client", "job", "task"]

    def get_multiple_sections(self, obj: Note) -> str:
        return str(obj.get_related_objects_as_dict)
        # return format_html(f'<pre><code class="language-json">{obj.get_multiple_sections}</code></pre>')
