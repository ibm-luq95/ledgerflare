from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from django.db.models.signals import pre_init, post_init

DEBUG = config("DEBUG", cast=bool)

ADMINS = [("Ibrahim Luqman", "ibm_luq995@outlook.com")]
MANAGERS = [("Ibrahim Luqman", "ibm_luq995@outlook.com")]


AUTH_PASSWORD_VALIDATORS = [
    {
        # Checks the similarity between the password and a set of attributes of the user.
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {
            "user_attributes": ("email", "first_name", "last_name"),
            "max_similarity": 0.7,
        },
    },
    {
        # Checks whether the password meets a minimum length.
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        # Checks whether the password occurs in a list of common passwords
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        # Checks whether the password isn’t entirely numeric
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
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
        "OPTIONS": {"client_encoding": config("DB_CLIENT_ENCODING", cast=str)},
    }
}

# Django production deployment settings
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", cast=bool)
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", cast=bool)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config("SECURE_HSTS_INCLUDE_SUBDOMAINS", cast=bool)
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", cast=bool)
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", cast=bool)
SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", cast=bool)
USE_X_FORWARDED_HOST = config("USE_X_FORWARDED_HOST", cast=bool)

# OWSP recommendation security configs
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
# SECURE_PROXY_SSL_HEADER = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if config("SENTRY_IS_ENABLED", cast=bool) is True:
    sentry_sdk.init(
        dsn=config("SENTRY_SDK_DSN", cast=str),
        integrations=[
            DjangoIntegration(
                transaction_style="url",
                middleware_spans=True,
                signals_spans=True,
                signals_denylist=[
                    pre_init,
                    post_init,
                ],
                cache_spans=False,
            )
        ],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
        environment="production",
        send_default_pii=True,
        # debug=True
    )

# Start from base logging
LOGGING = LOGGING_BASE.copy()
LOGGING["handlers"] = LOGGING["handlers"].copy()  # Allow adding new handlers

# Add file handlers
LOGGING["handlers"]["file_error"] = {
    "level": "ERROR",
    "class": "logging.FileHandler",
    "filename": LOGS_FOLDER / "bw_errors.log",
    "formatter": "verbose_json",
}

LOGGING["handlers"]["file_warning"] = {
    "level": "WARNING",
    "class": "logging.FileHandler",
    "filename": LOGS_FOLDER / "bw_warning.log",
    "formatter": "verbose_json",
}

LOGGING["handlers"]["file_app_rotating"] = {
    "level": "INFO",
    "class": "logging.handlers.TimedRotatingFileHandler",
    "when": "midnight",
    "interval": 1,
    "backupCount": 7,
    "filename": LOGS_FOLDER / "app.log",
    "formatter": "verbose_json",
}

# 🔽 Admin email handler is COMMENTED OUT — disabled for now
"""
LOGGING["handlers"]["email_admin"] = {
    "level": "ERROR",
    "class": "django.utils.log.AdminEmailHandler",
    "include_html": False,
}
"""

# Update root logger to handle all uncaught logs
LOGGING["root"] = {
    "handlers": ["file_app_rotating", "file_warning", "file_error"],
    "level": "INFO",
}

# bw_logger: main app logger
LOGGING["loggers"]["bw_logger"] = {
    "handlers": ["file_app_rotating", "file_warning", "file_error"],
    "level": "INFO",
    "propagate": False,
}

# Log django.request errors
LOGGING["loggers"]["django.request"] = {
    "handlers": ["file_error"],
    "level": "ERROR",
    "propagate": False,
}
