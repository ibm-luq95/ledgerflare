# -*- coding: utf-8 -*-#
import json

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.template import Template, Context
from django.urls import reverse_lazy, reverse
from django.utils.safestring import mark_safe

# JavaScript template: directly assign JSON as JS object
JS_SETTINGS_TEMPLATE_STR = "window.settings = {{ json_data }};"

# Compile once at startup
JS_SETTINGS_TEMPLATE = Template(JS_SETTINGS_TEMPLATE_STR)


# @cache_page(60 * 15)  # Cache for 15 minutes
# @vary_on_headers("Cookie")  # Vary by login state (different user = different cache)
def js_settings(request):
    """
    Returns a JavaScript file that sets `window.settings` with selected Django settings and request data.
    """
    # Build the data dictionary
    data = {
        "DEBUG": settings.DEBUG,
        "FETCHURLNAMEURL": reverse("core:api:fetch-url"),  # Ensure this URL name exists
        "CURRENTUSER": str(request.user.pk) if request.user.is_authenticated else None,
    }

    # Serialize to JSON string
    json_data = json.dumps(data)

    # Render template with trusted (safe) JSON
    context = Context({"json_data": mark_safe(json_data)})
    content = JS_SETTINGS_TEMPLATE.render(context)

    return HttpResponse(
        content=content,
        content_type="application/javascript; charset=UTF-8",
    )


# views.py


def custom_404_view(request):
    return render(request, "core/errors/404.html", status=404)


def custom_500_view(request):
    return render(request, "core/errors/500.html", status=404)
