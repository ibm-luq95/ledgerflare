from django.views.generic import TemplateView


class BankRegisterView(TemplateView):
    template_name = "client/bank_register.html"
