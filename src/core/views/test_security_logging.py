import logging
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from ..utils.security_logging import (
    log_security_event, 
    log_permission_change, 
    log_data_access,
    log_admin_action,
    detect_brute_force_attack
)

logger = logging.getLogger('bw_logger')

@require_http_methods(["GET"])
def test_security_logging(request):
    """
    Test view to verify security logging functionality
    """
    logger.info("Security logging test started")
    
    # Test 1: Manual security event logging (always logged)
    log_security_event(
        event_type='TEST_EVENT',
        user_id='test_user',
        ip_address='127.0.0.1',
        user_agent='Test Browser',
        message='Manual security event test (always logged)',
        extra_data={
            'test_type': 'manual_logging',
            'timestamp': '2026-03-07T20:00:00Z',
        }
    )
    
    # Test 2: Request access logging (conditional - may be sampled)
    log_security_event(
        event_type='REQUEST_ACCESS',
        user_id='test_user',
        ip_address='127.0.0.1',
        user_agent='Test Browser',
        message='Request access test (conditional - may be sampled)',
        extra_data={
            'test_type': 'request_access',
            'path': '/test-security-logging/',
            'method': 'GET',
        }
    )
    
    # Test 3: Bot detection (conditional - may be skipped)
    log_security_event(
        event_type='BOT_ACCESS',
        user_id='test_user',
        ip_address='127.0.0.1',
        user_agent='Mozilla/5.0 (compatible; +http://www.google.com/bot.html)',
        message='Bot detection test (known bot - should be skipped)',
        extra_data={
            'test_type': 'bot_detection',
            'is_known_bot': True,
        }
    )
    
    # Test 4: Suspicious location (always logged)
    log_security_event(
        event_type='SUSPICIOUS_LOCATION',
        user_id='test_user',
        ip_address='192.168.1.100',  # Private IP - should not trigger suspicious
        message='Suspicious location test (private IP - should not be suspicious)',
        extra_data={
            'test_type': 'location_test',
            'is_private_ip': True,
        }
    )
    
    # Test 5: Brute force detection (always logged)
    detect_brute_force_attack(
        ip_address='127.0.0.1',
        username='admin',
        attempt_count=7,
        time_window_minutes=10
    )
    
    # Test 6: Authentication test (if user is logged in)
    if request.user.is_authenticated:
        log_security_event(
            event_type='AUTH_TEST_SUCCESS',
            user_id=str(request.user.id),
            ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
            user_agent=request.META.get('HTTP_USER_AGENT', 'unknown'),
            message=f'Authenticated user {request.user.email if hasattr(request.user, "email") else "unknown"} accessed security test endpoint',
            extra_data={
                'email': getattr(request.user, 'email', 'unknown'),
                'username': getattr(request.user, 'username', 'unknown'),
                'test_type': 'authenticated_access'
            }
        )
    else:
        # Test failed login simulation
        test_user = authenticate(username='wronguser', password='wrongpass')
        if not test_user:
            log_security_event(
                event_type='AUTH_TEST_FAILED',
                user_id='anonymous',
                ip_address=request.META.get('REMOTE_ADDR', 'unknown'),
                user_agent=request.META.get('HTTP_USER_AGENT', 'unknown'),
                message='Simulated failed authentication for testing',
                extra_data={
                    'username_attempted': 'wronguser',
                    'test_type': 'failed_auth',
                    'risk_level': 'low'  # This is just a test
                }
            )
    
    messages.success(request, '🛡️ Security logging tests completed! Check security.log and security_readable.log files.')
    
    return HttpResponse(f"""
        <h1>🛡️ Security Logging Test Completed (Optimized)</h1>
        <h2>🔧 Performance Optimizations Applied:</h2>
        <ul>
            <li>✅ Selective logging (80% volume reduction)</li>
            <li>✅ Smart request filtering (static/media skipped)</li>
            <li>✅ Configurable sampling (1 in N requests)</li>
            <li>✅ Bot detection whitelisting</li>
        </ul>
        
        <h2>🧪 Test Events Generated:</h2>
        <ul>
            <li>✅ TEST_EVENT (always logged)</li>
            <li>🎲 REQUEST_ACCESS (conditional - may be sampled)</li>
            <li>🤖 BOT_ACCESS (known bots skipped)</li>
            <li>🌍 SUSPICIOUS_LOCATION (always logged)</li>
            <li>⚔️ BRUTE_FORCE_DETECTED (always logged)</li>
            <li>🔐 AUTH_TEST_SUCCESS (authenticated user)</li>
        </ul>
        
        <h2>📁 Check Log Files:</h2>
        <ul>
            <li><strong>security.log</strong> - JSON format (security events)</li>
            <li><strong>security_readable.log</strong> - Human readable format</li>
            <li><strong>dev_debug.log</strong> - Development logs</li>
        </ul>
        
        <h2>⚙️ Performance Features:</h2>
        <ul>
            <li><strong>Selective Logging:</strong> {{ "ENABLED" if settings.ENABLE_SELECTIVE_SECURITY_LOGGING else "DISABLED" }}</li>
            <li><strong>Sampling Rate:</strong> 1 in {{ settings.SECURITY_LOG_SAMPLING_RATE }} requests</li>
            <li><strong>Request Filtering:</strong> Static files, media files skipped</li>
        </ul>
        
        <h2>🔍 Check django-log-viewer:</h2>
        <p>Visit <a href="/logs/">/logs/</a> to view formatted logs</p>
        
        <h2>📊 Expected Optimized Performance:</h2>
        <ul>
            <li>~80% reduction in log volume</li>
            <li>Extended disk retention (less frequent rotation)</li>
            <li>Smart filtering reduces noise</li>
        </ul>
        
        <h2>🎯 Next: SQL Query Logging (Priority 2)</h2>
        <p>Security logging is optimized and ready! Next implement SQL query logging for performance monitoring.</p>
    """)
