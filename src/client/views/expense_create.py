from django.views.generic import TemplateView


class ExpenseCreateView(TemplateView):
    template_name = "client/expense_create.html"
