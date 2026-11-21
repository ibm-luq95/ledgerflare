from .config import app_settings

environment = app_settings.STAGE_ENVIRONMENT

if environment == "DEV":
    from .dev import *
elif environment == "PRODUCTION":
    from .production import *
elif environment == "TEST":
    from .test import *
elif environment == "LOCAL":
    from .local import *
elif environment == "STAGE":
    from .stage import *
elif environment == "LOCAL_DEV":
    from .local_dev import *
