import logging
import json
from typing import Optional
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.contrib.auth import get_user
from django.contrib.sessions.models import Session
import ipaddress
import random

# Get security logger
security_logger = logging.getLogger('security_logger')

def should_log_security_event(event_type: str, request: HttpRequest) -> bool:
    """Determine if security event should be logged based on configuration"""
    if not settings.ENABLE_SELECTIVE_SECURITY_LOGGING:
        return True  # If selective logging disabled, log everything
    
    # Always log critical events
    if event_type in settings.ALWAYS_LOG_SECURITY_EVENTS:
        return True
    
    # For conditional events, check additional criteria
    if event_type in settings.CONDITIONAL_SECURITY_EVENTS:
        # Skip high-volume, low-risk requests
        skip_patterns = ['/static/', '/media/', '/favicon.ico', '/health/', '/logs/']
        if any(request.path.startswith(pattern) for pattern in skip_patterns):
            return False
        
        # Only log suspicious activities
        if event_type == 'REQUEST_ACCESS':
            return is_suspicious_location(get_client_ip(request))
        
        # Only log unknown bots (skip Google, Bing, etc.)
        if event_type == 'BOT_ACCESS':
            user_agent = get_user_agent_string(request)
            known_bots = ['googlebot', 'bingbot', 'slurp', 'spider']
            return not any(bot in user_agent.lower() for bot in known_bots)
        
        return True

def should_sample_request() -> bool:
    """Implement sampling to reduce log volume"""
    if not settings.ENABLE_SELECTIVE_SECURITY_LOGGING:
        return False  # No sampling if selective logging disabled
    
    # Log 1 in N requests (configurable)
    return random.randint(1, settings.SECURITY_LOG_SAMPLING_RATE) == 1

def get_client_ip(request: HttpRequest) -> str:
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or 'unknown'

def get_user_agent_string(request: HttpRequest) -> str:
    """Extract user agent string from request"""
    return request.META.get('HTTP_USER_AGENT', 'unknown')

def parse_user_agent(user_agent_string: str) -> dict:
    """Parse user agent to extract useful information (simplified version)"""
    # Simple parsing without external dependencies
    ua_lower = user_agent_string.lower()
    
    # Detect common browsers and bots
    is_bot = any(bot in ua_lower for bot in [
        'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget', 
        'python-requests', 'httpie', 'postman'
    ])
    
    is_mobile = any(mobile in ua_lower for mobile in [
        'mobile', 'android', 'iphone', 'ipad', 'tablet'
    ])
    
    # Extract browser name (simplified)
    browser = 'unknown'
    if 'chrome' in ua_lower:
        browser = 'Chrome'
    elif 'firefox' in ua_lower:
        browser = 'Firefox'
    elif 'safari' in ua_lower and 'chrome' not in ua_lower:
        browser = 'Safari'
    elif 'edge' in ua_lower:
        browser = 'Edge'
    elif 'opera' in ua_lower:
        browser = 'Opera'
    
    # Extract OS (simplified)
    os_name = 'unknown'
    if 'windows' in ua_lower:
        os_name = 'Windows'
    elif 'mac' in ua_lower or 'darwin' in ua_lower:
        os_name = 'macOS'
    elif 'linux' in ua_lower:
        os_name = 'Linux'
    elif 'android' in ua_lower:
        os_name = 'Android'
    elif 'ios' in ua_lower or 'iphone' in ua_lower or 'ipad' in ua_lower:
        os_name = 'iOS'
    
    return {
        'browser': browser,
        'os': os_name,
        'device': 'mobile' if is_mobile else 'desktop',
        'is_bot': is_bot,
        'is_mobile': is_mobile,
        'raw_string': user_agent_string[:100],  # Truncate for logging
    }

def is_suspicious_location(ip: str) -> bool:
    """Check if IP is from suspicious location (basic implementation)"""
    # This is a placeholder - in production, integrate with GeoIP2
    try:
        # Basic checks for private/internal IPs
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local
    except:
        return True  # Treat unknown IPs as suspicious

class SecurityLoggingMiddleware:
    """Middleware to log security events"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Process request
        response = self.get_response(request)
        
        # Get request information
        user = get_user(request)
        user_id = user.id if user and user.is_authenticated else 'anonymous'
        ip_address = get_client_ip(request)
        user_agent_string = get_user_agent_string(request)
        user_agent_info = parse_user_agent(user_agent_string)
        
        # Safely get content length
        try:
            content_length = len(request.body) if hasattr(request, 'body') else 0
        except:
            content_length = 0
        
        # Log security event for each request
        if should_log_security_event('REQUEST_ACCESS', request) and should_sample_request():
            self._log_security_event(
                event_type='REQUEST_ACCESS',
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent_string,
                message=f"Accessed {request.method} {request.get_full_path()}",
                extra_data={
                    'method': request.method,
                    'path': request.get_full_path(),
                    'query_params': dict(request.GET),
                    'is_ajax': request.headers.get('X-Requested-With') == 'XMLHttpRequest',
                    'content_length': content_length,
                    'user_agent_info': user_agent_info,
                    'sampled': True,  # Mark as sampled
                }
            )
        
        # Log suspicious activities
        if is_suspicious_location(ip_address):
            self._log_security_event(
                event_type='SUSPICIOUS_LOCATION',
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent_string,
                message=f"Access from suspicious IP location: {ip_address}",
                extra_data={'risk_level': 'medium'}
            )
        
        # Log bot access
        if user_agent_info['is_bot']:
            self._log_security_event(
                event_type='BOT_ACCESS',
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent_string,
                message=f"Bot access detected: {user_agent_info['browser']}",
                extra_data={'risk_level': 'low'}
            )
        
        return response
    
    def _log_security_event(self, event_type: str, user_id: str, ip_address: str, 
                         user_agent: str, message: str, extra_data: Optional[dict] = None):
        """Log a security event with structured data"""
        # Create log record with extra context
        extra = {
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
        }
        
        if extra_data:
            extra.update(extra_data)
        
        security_logger.info(message, extra=extra)

# Helper function for manual security logging
def log_security_event(event_type: str, user_id: str = 'system', ip_address: str = 'system',
                    user_agent: str = 'system', message: str = '', 
                    extra_data: Optional[dict] = None):
    """Helper function to log security events from anywhere in the code"""
    extra = {
        'event_type': event_type,
        'user_id': user_id,
        'ip_address': ip_address,
        'user_agent': user_agent,
    }
    
    if extra_data:
        extra.update(extra_data)
    
    security_logger.info(message, extra=extra)
