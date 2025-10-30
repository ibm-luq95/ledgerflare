from django.views.generic import TemplateView


class JournalEntryView(TemplateView):
    template_name = "client/journal_entry.html"
