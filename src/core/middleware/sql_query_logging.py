"""
SQL Query Logging Middleware for Performance Monitoring
"""
import logging
import time
import hashlib
from typing import Optional
from django.conf import settings
from django.db import connection
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse

# Get SQL query logger
sql_logger = logging.getLogger('sql_query_logger')

class SQLQueryLoggingMiddleware:
    """Middleware to log SQL queries with performance monitoring"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.query_count = 0
        self.start_time = time.time()
        
    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        
        # Only log if SQL logging is enabled
        if settings.ENABLE_SQL_QUERY_LOGGING:
            self._log_query_summary()
        
        return response
    
    def _log_query_summary(self):
        """Log summary of SQL queries for this request"""
        if self.query_count > 0:
            duration_ms = (time.time() - self.start_time) * 1000
            
            # Get query details
            queries = connection.queries
            total_rows = 0
            slow_queries = []
            query_details = []
            
            for query in queries:
                sql = query.get('sql', '')
                duration = float(query.get('time', 0)) * 1000  # Convert to ms
                
                # Count rows affected (simplified)
                row_count = len(sql.split()) if sql else 0
                total_rows += row_count
                
                # Check if query is slow
                is_slow = duration > settings.SLOW_QUERY_THRESHOLD_MS
                if is_slow:
                    slow_queries.append({
                        'sql': sql[:200],  # Truncate for readability
                        'duration_ms': round(duration, 2),
                        'row_count': row_count,
                    })
                
                # Generate query fingerprint
                query_hash = self._generate_query_fingerprint(sql)
                
                query_details.append({
                    'sql': sql[:200],  # Truncate for readability
                    'duration_ms': round(duration, 2),
                    'row_count': row_count,
                    'is_slow': is_slow,
                    'query_hash': query_hash,
                })
            
            # Determine if we should log this request (sampling)
            should_log = self._should_log_request()
            
            if should_log:
                # Log the query summary
                self._log_sql_queries(
                    query_count=self.query_count,
                    total_duration_ms=duration_ms,
                    total_rows=total_rows,
                    slow_count=len(slow_queries),
                    slow_queries=slow_queries[:5],  # Limit to top 5 slow queries
                    query_details=query_details[:10],  # Limit to top 10 queries
                )
    
    def _should_log_request(self) -> bool:
        """Determine if this request should be logged based on sampling"""
        if settings.SQL_QUERY_SAMPLING_RATE <= 1:
            return True  # Log all requests if rate is 1
        
        # Sample 1 in N requests
        return (self.query_count % settings.SQL_QUERY_SAMPLING_RATE) == 0
    
    def _generate_query_fingerprint(self, sql: str) -> str:
        """Generate a fingerprint for the query by removing literals and whitespace"""
        if not sql:
            return 'empty'
        
        # Simple fingerprinting - remove common literals and normalize whitespace
        fingerprint = sql.lower()
        fingerprint = fingerprint.replace("'", "").replace('"', "")
        fingerprint = ' '.join(fingerprint.split())  # Normalize whitespace
        
        # Remove common patterns that vary (timestamps, UUIDs, etc.)
        import re
        fingerprint = re.sub(r'\d{4}-\d{2}-\d{2}', 'DATE', fingerprint)
        fingerprint = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', 'UUID', fingerprint)
        fingerprint = re.sub(r'\b\d+\b', 'NUM', fingerprint)
        
        return hashlib.md5(fingerprint.encode()).hexdigest()[:8]
    
    def _log_sql_queries(self, query_count: int, total_duration_ms: float, 
                      total_rows: int, slow_count: int, slow_queries: list,
                      query_details: list):
        """Log SQL query information"""
        message = f"SQL Query Summary: {query_count} queries, {total_duration_ms:.2f}ms total, {total_rows} rows affected"
        
        extra_data = {
            'query_count': query_count,
            'total_duration_ms': round(total_duration_ms, 2),
            'total_rows': total_rows,
            'slow_count': slow_count,
            'slow_queries': slow_queries,
            'query_details': query_details,
            'threshold_ms': settings.SLOW_QUERY_THRESHOLD_MS,
        }
        
        # Add EXPLAIN plan if enabled and there are slow queries
        if slow_queries and settings.ENABLE_EXPLAIN_PLANS:
            try:
                with connection.cursor() as cursor:
                    # Get EXPLAIN plan for first slow query
                    first_slow = slow_queries[0]
                    explain_sql = f"EXPLAIN ANALYZE {first_slow['sql']}"
                    cursor.execute(explain_sql)
                    explain_plan = cursor.fetchall()
                    extra_data['explain_plan'] = str(explain_plan)
            except Exception as e:
                extra_data['explain_error'] = str(e)
        
        sql_logger.info(message, extra=extra_data)


class QueryLogger:
    """Context manager for individual query logging"""
    
    def __init__(self, sql: str, params: tuple = None):
        self.sql = sql
        self.params = params
        self.start_time = time.time()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        duration_ms = (time.time() - self.start_time) * 1000
        
        # Only log if enabled and not excluded model
        if settings.ENABLE_SQL_QUERY_LOGGING and not self._is_excluded_model():
            sql_logger.info(
                f"Query executed in {duration_ms:.2f}ms",
                extra={
                    'sql': self.sql[:200],  # Truncate for readability
                    'duration_ms': round(duration_ms, 2),
                    'row_count': 0,  # Would need actual execution to get this
                    'is_slow': duration_ms > settings.SLOW_QUERY_THRESHOLD_MS,
                    'query_hash': self._generate_query_fingerprint(self.sql),
                    'params': str(self.params)[:100] if self.params else None,
                }
            )
    
    def _is_excluded_model(self) -> bool:
        """Check if this query should be excluded based on model names"""
        if not self.sql:
            return False
        
        excluded_models = settings.EXCLUDE_SQL_MODELS.split(',')
        return any(model.lower() in self.sql.lower() for model in excluded_models)


def log_sql_query(sql: str, params: tuple = None, duration_ms: float = None):
    """Convenience function to log individual SQL queries"""
    if not settings.ENABLE_SQL_QUERY_LOGGING:
        return
    
    query_logger.info(
        f"SQL Query: {duration_ms or 'unknown'}ms",
        extra={
            'sql': sql[:200],  # Truncate for readability
            'duration_ms': round(duration_ms, 2) if duration_ms else None,
            'row_count': 0,  # Would need actual execution to get this
            'is_slow': (duration_ms or 0) > settings.SLOW_QUERY_THRESHOLD_MS,
            'query_hash': QueryLogger(sql)._generate_query_fingerprint(sql),
            'params': str(params)[:100] if params else None,
        }
    )
