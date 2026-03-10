import logging
from typing import Optional
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.contrib.sessions.models import Session
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User

from core.middleware.security_logging import log_security_event

# Get security logger
security_logger = logging.getLogger('security_logger')

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log successful user login"""
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    
    log_security_event(
        event_type='LOGIN_SUCCESS',
        user_id=str(user.id),
        ip_address=ip_address,
        user_agent=user_agent,
        message=f"User {user.email} logged in successfully",
        extra_data={
            'email': user.email,
            'username': user.email,
            'login_method': 'password',  # Could be extended for OAuth, etc.
            'timestamp': user.last_login.isoformat() if user.last_login else None,
        }
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout"""
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    
    log_security_event(
        event_type='LOGOUT_SUCCESS',
        user_id=str(user.id) if user else 'anonymous',
        ip_address=ip_address,
        user_agent=user_agent,
        message=f"User {user.email if user else 'anonymous'} logged out",
        extra_data={
            'email': user.email if user else None,
            'username': user.username if user else None,
            'logout_method': 'manual',
        }
    )

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Log failed login attempt"""
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    username = credentials.get('username', 'unknown')
    
    log_security_event(
        event_type='LOGIN_FAILED',
        user_id='anonymous',
        ip_address=ip_address,
        user_agent=user_agent,
        message=f"Failed login attempt for username: {username}",
        extra_data={
            'username_attempted': username,
            'failure_reason': 'invalid_credentials',
            'risk_level': 'high',
        }
    )

@receiver(post_save, sender=User)
def log_user_changes(sender, instance, created, **kwargs):
    """Log user model changes"""
    if created:
        log_security_event(
            event_type='USER_CREATED',
            user_id=str(instance.id),
            ip_address='system',
            user_agent='system',
            message=f"New user created: {instance.email}",
            extra_data={
                'user_email': instance.email,  # Use user_email key to avoid conflicts
                'username': instance.username,
                'is_staff': instance.is_staff,
                'is_superuser': instance.is_superuser,
                'date_joined': instance.date_joined.isoformat() if instance.date_joined else None,
            }
        )
    else:
        # Log important field changes
        changed_fields = []
        if hasattr(instance, '_original_fields'):
            for field_name, original_value in instance._original_fields.items():
                current_value = getattr(instance, field_name)
                if original_value != current_value:
                    changed_fields.append({
                        'field': field_name,
                        'old_value': str(original_value),
                        'new_value': str(current_value),
                    })
        
        if changed_fields:
            log_security_event(
                event_type='USER_UPDATED',
                user_id=str(instance.id),
                ip_address='system',
                user_agent='system',
                message=f"User {instance.email} updated: {[f['field'] for f in changed_fields]}",
                extra_data={
                    'email': instance.email,
                    'changed_fields': changed_fields,
                    'is_sensitive': any(f['field'] in ['email', 'password', 'is_staff', 'is_superuser'] for f in changed_fields),
                }
            )

def log_permission_change(user_id: str, permission_type: str, old_value: str, new_value: str, 
                        changed_by: str = 'system', reason: str = ''):
    """Log permission changes"""
    log_security_event(
        event_type='PERMISSION_CHANGED',
        user_id=user_id,
        ip_address='system',
        user_agent='system',
        message=f"Permission {permission_type} changed from {old_value} to {new_value}",
        extra_data={
            'permission_type': permission_type,
            'old_value': old_value,
            'new_value': new_value,
            'changed_by': changed_by,
            'reason': reason,
            'is_sensitive': True,
        }
    )

def log_data_access(user_id: str, model_name: str, record_id: str, 
                  action: str = 'view', ip_address: str = 'system'):
    """Log access to sensitive data"""
    log_security_event(
        event_type='DATA_ACCESS',
        user_id=user_id,
        ip_address=ip_address,
        user_agent='system',
        message=f"User accessed {model_name} record {record_id} - {action}",
        extra_data={
            'model_name': model_name,
            'record_id': record_id,
            'action': action,  # view, edit, delete, export
            'is_sensitive': True,
        }
    )

def log_admin_action(user_id: str, action: str, target: str, 
                 details: dict = None, ip_address: str = 'system'):
    """Log administrative actions"""
    log_security_event(
        event_type='ADMIN_ACTION',
        user_id=user_id,
        ip_address=ip_address,
        user_agent='system',
        message=f"Admin performed {action} on {target}",
        extra_data={
            'action': action,
            'target': target,
            'details': details or {},
            'is_sensitive': True,
        }
    )

# Rate limiting detection
def detect_brute_force_attack(ip_address: str, username: str, attempt_count: int, 
                          time_window_minutes: int = 15):
    """Detect potential brute force attack"""
    if attempt_count >= 5:  # Threshold for brute force detection
        risk_level = 'critical' if attempt_count >= 10 else 'high'
        log_security_event(
            event_type='BRUTE_FORCE_DETECTED',
            user_id='anonymous',
            ip_address=ip_address,
            user_agent='unknown',
            message=f"Potential brute force attack on {username}: {attempt_count} attempts in {time_window_minutes} minutes",
            extra_data={
                'target_username': username,
                'attempt_count': attempt_count,
                'time_window_minutes': time_window_minutes,
                'risk_level': risk_level,
            }
        )
        return True
    return False
