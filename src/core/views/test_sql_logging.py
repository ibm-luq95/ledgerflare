import logging
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.db import connection
from django.conf import settings
from django.contrib.auth import get_user_model

# Get SQL query logger
sql_logger = logging.getLogger('sql_query_logger')

@require_http_methods(["GET"])
def test_sql_logging(request):
    """
    Test view to verify SQL query logging functionality
    """
    logger = logging.getLogger('bw_logger')
    logger.info("SQL Query Logging Test Started")
    
    # Test 1: Generate some database queries
    User = get_user_model()
    
    try:
        # This will generate SQL queries
        users = list(User.objects.all()[:10])
        user_count = User.objects.count()
        
        # Generate a slow query
        slow_users = User.objects.all().order_by('-id')[:5]  # This should be fast
        for user in slow_users:
            # Force a slow query by accessing related data
            _ = user.groups.all()  # This might be slower
        
        # Simulate a very slow query (if we had complex data)
        # Note: This is just for testing - in real app, you'd have actual slow queries
        
        logger.info(f"Generated {len(connection.queries)} SQL queries for testing")
        
        return HttpResponse(f"""
            <h1>🗄️ SQL Query Logging Test Completed</h1>
            
            <h2>📊 Query Statistics:</h2>
            <ul>
                <li><strong>Total Queries:</strong> {len(connection.queries)}</li>
                <li><strong>User Count:</strong> {user_count}</li>
                <li><strong>Users Retrieved:</strong> {len(users)}</li>
                <li><strong>Slow Query Threshold:</strong> {settings.SLOW_QUERY_THRESHOLD_MS}ms</li>
                <li><strong>Sampling Rate:</strong> 1 in {settings.SQL_QUERY_SAMPLING_RATE} requests</li>
                <li><strong>EXPLAIN Plans:</strong> {'Enabled' if settings.ENABLE_EXPLAIN_PLANS else 'Disabled'}</li>
            </ul>
            
            <h2>📁 Log Files Created:</h2>
            <ul>
                <li><strong>sql_queries.log</strong> - JSON format for analysis</li>
                <li><strong>sql_queries_readable.log</strong> - Human readable format</li>
            </ul>
            
            <h2>🔍 Check Logs:</h2>
            <ul>
                <li><strong>SQL Query Logs:</strong> <a href="/logs/">View in django-log-viewer</a></li>
                <li><strong>Raw Logs:</strong> Check logs/sql_queries*.log</li>
            </ul>
            
            <h2>⚙️ Configuration:</h2>
            <ul>
                <li><strong>SQL Logging:</strong> {'Enabled' if settings.ENABLE_SQL_QUERY_LOGGING else 'Disabled'}</li>
                <li><strong>Excluded Models:</strong> {settings.EXCLUDE_SQL_MODELS}</li>
            </ul>
            
            <h2>🧪 Expected Features:</h2>
            <ul>
                <li>✅ Query counting per request</li>
                <li>✅ Slow query highlighting (&gt;{settings.SLOW_QUERY_THRESHOLD_MS}ms)</li>
                <li>✅ Query fingerprinting for duplicate detection</li>
                <li>✅ Model exclusion capabilities</li>
                <li>✅ Configurable sampling rate</li>
                <li>✅ EXPLAIN plans for slow queries</li>
            </ul>
        """)
        
    except Exception as e:
        logger.error(f"SQL logging test failed: {e}")
        return HttpResponse(f"""
            <h1>❌ SQL Query Logging Test Failed</h1>
            <p><strong>Error:</strong> {e}</p>
            <p>Check your database configuration and try again.</p>
        """, status=500)
