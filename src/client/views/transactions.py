from django.views.generic import TemplateView


class ClientTransactionListView(TemplateView):
    template_name = "client/transaction_list.html"
