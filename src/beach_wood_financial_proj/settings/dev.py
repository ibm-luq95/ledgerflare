import mimetypes

from .base import *

# Add color formatter
try:
    from colorlog import ColoredFormatter

    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


mimetypes.add_type("application/javascript", ".js", True)

DEBUG = config("DEBUG", cast=bool)

CSRF_USE_SESSIONS = False

INSTALLED_APPS = INSTALLED_APPS + [
    "django.contrib.admindocs",
    "debug_toolbar",
    "template_profiler_panel",
    "debugtools",
    "debug_permissions",
    "django_model_info.apps.DjangoModelInfoConfig",
    # "silk",
    # "django_pdb",
    # "request_viewer",
]
# INSTALLED_APPS.insert(0, "django_pdb")

MIDDLEWARE = MIDDLEWARE + [
    # "request_viewer.middleware.RequestViewerMiddleware",
    # "request_viewer.middleware.ExceptionMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "debugtools.middleware.XViewMiddleware",
    "django.contrib.admindocs.middleware.XViewMiddleware",
    # "django_pdb.middleware.PdbMiddleware",
    # "silk.middleware.SilkyMiddleware",
]

# Database configurations
DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE", cast=str),
        "NAME": config("DB_NAME", cast=str),
        "USER": config("DB_USER", cast=str),
        "PASSWORD": config("DB_PASSWORD", cast=str),
        "HOST": config("DB_HOST", cast=str),
        "PORT": config("DB_PORT", cast=str),
        "CONN_MAX_AGE": None,
        "ATOMIC_REQUESTS": True,
        "OPTIONS": {
            "client_encoding": config("DB_CLIENT_ENCODING", cast=str),
            "server_side_binding": True,
        },
        "TEST": {
            "NAME": "testing_beachwoodfinancial_development_db",
            "MIGRATE": False,
        },
    }
}
# if config("DB_ENGINE", cast=str) == "django.db.backends.mysql":
# 	DATABASES["default"]["OPTIONS"] = {"init_command": "SET default_storage_engine=INNODB"}
# elif config("DB_ENGINE", cast=str) == "django.db.backends.postgresql":
# 	DATABASES["default"]["OPTIONS"] = {
# 		"client_encoding": config("DB_CLIENT_ENCODING", cast=str),
# 		"server_side_binding": True,
# 	}
# check if the code run locally or on the host
# if config("WHEREAMI", cast=str) == "LOCAL":
# DATABASES["default"]["OPTIONS"].update({"read_default_file": "/opt/lampp/etc/my.cnf"})
# DATABASES["default"]["OPTIONS"].update({"read_default_file": "/etc/my.cnf"})

TEMPLATES[0]["OPTIONS"]["builtins"].extend(
    [
        "debugtools.templatetags.debugtools_tags",
        "core.templatetags.development_tags",
    ]
)

# DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS = True
# Djagno Debug Toolbar
INTERNAL_IPS = config("INTERNAL_IPS", cast=Csv())
DISABLE_PANELS = {}

DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.history.HistoryPanel",
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
    "debugtools.panels.ViewPanel",
    "debug_toolbar.panels.templates.TemplatesPanel",
    "debug_toolbar.panels.cache.CachePanel",
    "debug_toolbar.panels.signals.SignalsPanel",
    "debug_toolbar.panels.logging.LoggingPanel",
    "debug_toolbar.panels.redirects.RedirectsPanel",
    # "debug_toolbar.panels.profiling.ProfilingPanel",
    "template_profiler_panel.panels.template.TemplateProfilerPanel",
]

SHOW_COLLAPSED = True


def show_toolbar(request):
    return True


DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": show_toolbar, "IS_RUNNING_TESTS": False}

GRAPH_MODELS = {"all_applications": True, "group_models": True}
# GRAPH_MODELS = {'app_labels': ["client"]}

# django-request-viewer configs
REQUEST_VIEWER = {"LIVE_MONITORING": False, "WHITELISTED_PATH": []}


# django-silk settings
# SILKY_PYTHON_PROFILER = True
# SILKY_PYTHON_PROFILER_BINARY = True
# SILKY_META = True
# # SILKY_ANALYZE_QUERIES = True
# # SILKY_EXPLAIN_FLAGS = {'format':'JSON', 'costs': True}
# SILKY_PERMISSIONS = lambda user: user.is_superuser
# SILKY_AUTHENTICATION = True  # User must login
# SILKY_AUTHORISATION = True  # User must have permissions
# SILKY_PYTHON_PROFILER_EXTENDED_FILE_NAME = True
# SILKY_PYTHON_PROFILER_RESULT_PATH = BASE_DIR / "media" / "profiles"

# Logging configs
# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "formatters": {
#         "verbose": {
#             "format": "{levelname} {asctime} {module} {message}",
#             "style": "{",
#         },
#     },
#     "handlers": {
#         "console": {
#             "level": "DEBUG",
#             "class": "logging.StreamHandler",
#             "formatter": "verbose",
#         },
#     },
#     "loggers": {
#         "django": {
#             "handlers": ["console"],
#             "level": "INFO",
#         },
#         "bw_log": {
#             "handlers": ["console"],
#             "level": "DEBUG",
#         },
#     },
# }

TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG

COMPONENTS = ComponentsSettings(
    autodiscover=True,
    reload_on_file_change=True,
    template_cache_size=2,
)
DJANGO_EASY_AUDIT_PROPAGATE_EXCEPTIONS = DEBUG
if HAS_COLORLOG:
    LOGGING_BASE["formatters"]["dev_color"] = {
        "()": "colorlog.ColoredFormatter",
        "format": (
            "{bold_black}{asctime}{reset} {log_color}{levelname}{reset} "
            "{blue}{pathname}:{lineno}{reset} :: {message}\n"
            "{log_color}Stack Trace:{reset} {exc_info}"  # New: Adds stack trace
        ),
        "style": "{",
        "log_colors": {
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    }

    LOGGING_BASE["handlers"]["console"]["formatter"] = "dev_color"
LOGGING = LOGGING_BASE.copy()

# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "formatters": {
#         "dev": {
#             "format": (
#                 "\033[36m{levelname}\033[0m \033[32m{asctime}\033[0m "
#                 "\033[34m{module}\033[0m:\033[33m{lineno}\033[0m ➜ \033[37m{message}\033[0m"
#             ),
#             "style": "{",
#             "datefmt": "%H:%M:%S",
#         }
#     },
#     "handlers": {
#         # Rich console output only
#         "console": {
#             "level": "DEBUG",
#             "class": "logging.StreamHandler",
#             "formatter": "dev",
#         },
#     },
#     "loggers": {
#         "django": {
#             "handlers": ["console"],
#             "level": "INFO",
#             "propagate": False,
#         },
#         "myapp": {
#             "handlers": ["console"],
#             "level": "DEBUG",
#             "propagate": False,
#         },
#     },
#     "root": {
#         "handlers": ["console"],
#         "level": "DEBUG",
#     },
# }
