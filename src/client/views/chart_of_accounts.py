from django.views.generic import TemplateView


class ChartOfAccountClientView(TemplateView):
    template_name = "client/chart_of_accounts.html"
