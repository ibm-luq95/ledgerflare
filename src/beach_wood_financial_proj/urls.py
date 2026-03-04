from core.views import js_settings
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import RedirectView
from django.views.i18n import JavaScriptCatalog

from core.views.core import custom_404_view, custom_500_view

# Custom 404 error view
handler404 = "core.views.error_404"
# Custom 500 error view
handler500 = "core.views.error_500"

static_and_media_path_urls = static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns = [
    # path("admin/", admin.site.urls),
    # path("admin/defender/", include("defender.urls")),  # defender admin
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    # path("", include("home.urls"), name="home-urls"),
    path("logs/", include("log_viewer.urls")),
    path("", RedirectView.as_view(url=reverse_lazy("auth:login")), name="home-url"),
    path("js-settings/", js_settings, name="js_settings"),
    path("core/", include("core.urls"), name="core-urls"),
    path("auth/", include("beach_wood_user.urls.auth"), name="auth-urls"),
    path("dashboard/", include("dashboard.urls"), name="dashboard-urls"),
    path("", include("django_components.urls")),
]

admin.site.index_title = _("LedgerFlare Administrator")
admin.site.site_header = _("LedgerFlare Solutions")
admin.site.site_title = _("LedgerFlare Administrator")

if settings.DEBUG:
    urlpatterns += static_and_media_path_urls
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))
    # urlpatterns.append(
    #     path("request-logs/", include("request_viewer.urls")),
    # )
    urlpatterns.append(path("admin/", admin.site.urls))
    urlpatterns.append(path("admin/doc/", include("django.contrib.admindocs.urls")))
    urlpatterns.append(path("test-500/", custom_500_view))
    urlpatterns.append(path("test-404/", custom_404_view))
    # urlpatterns.append(path("silk/", include("silk.urls", namespace="silk")))
    # urlpatterns.append(path("admin/", admin.site.urls))
else:
    urlpatterns.append(path("secret/", admin.site.urls))
