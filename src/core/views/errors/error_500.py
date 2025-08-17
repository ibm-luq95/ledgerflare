from django.http import HttpResponse
from django.shortcuts import redirect, render


def error_500(request):
    """
    Render the "core/errors/500.html" template with a status code of 500.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered HTTP response.

    """
    return render(request, "core/errors/500.html", status=500)
