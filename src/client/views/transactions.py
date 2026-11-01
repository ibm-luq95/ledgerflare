from __future__ import annotations

from django.views.generic import TemplateView

from core.views.mixins import BWLoginRequiredMixin


class ClientTransactionListView(BWLoginRequiredMixin, TemplateView):
    template_name = "client/transaction_list.html"
