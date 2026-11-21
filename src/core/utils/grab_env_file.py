# -*- coding: utf-8 -*-#
from typing import Any
from beach_wood_financial_proj.settings.config import app_settings

class DecoupleCompatibilityWrapper:
    """Wraps Pydantic Settings to behave like python-decouple's config object."""
    
    def __init__(self, settings_obj: Any):
        self._settings = settings_obj
        
    def __call__(self, key: str, cast: Any = None, default: Any = None) -> Any:
        if hasattr(self._settings, key):
            val = getattr(self._settings, key)
            # If the user passed Csv() as cast, we don't need to do anything since list is already parsed.
            # But if cast is list, or they want some specific type parsing, we can check.
            # In general, getattr returns the typed value from Pydantic Settings.
            return val
        if default is not None:
            return default
        raise KeyError(f"Key '{key}' not found in AppSettings schema.")

def grab_env_file(env_file_name: str = ".env") -> DecoupleCompatibilityWrapper:
    """Compatibility helper returning a wrapped settings schema instance."""
    return DecoupleCompatibilityWrapper(app_settings)
