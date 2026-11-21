from import_export import resources

from note.models import Note


class NoteResource(resources.ModelResource):
    class Meta:
        model = Note
