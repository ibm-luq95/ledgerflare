"""
SQL Query Logging Configuration
This file extends the base logging configuration with SQL query logging capabilities.
"""

from .base import LOGGING_BASE, LOGS_FOLDER, settings

# Add SQL query logger to existing configuration
SQL_LOGGING = {
    **LOGGING_BASE,
    "loggers": {
        **LOGGING_BASE.get("loggers", {}),
        
        # SQL Query Logger
        "sql_query_logger": {
            "handlers": ["sql_query_file_json", "sql_query_file_readable"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Add SQL query patterns to django-log-viewer
SQL_LOGGING_PATTERNS = [
    r'"duration_ms":',
    r'"sql":',
    r'"query_count":',
    r'"slow_count":',
    r'"total_duration_ms":',
    r'"threshold_ms":',
    r'"explain_plan":',
    r'"query_hash":',
    r"slow_queries",
    r"Query executed",
    r"SQL Query Summary",
    r"SLOW QUERY",
    r"EXPLAIN ANALYZE",
]

# Update django-log-viewer patterns to include SQL patterns
if hasattr(settings, 'LOG_VIEWER_PATTERNS'):
    settings.LOG_VIEWER_PATTERNS.extend(SQL_LOGGING_PATTERNS)
