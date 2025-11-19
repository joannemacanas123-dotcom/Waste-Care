from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service class for handling email notifications"""
    
    @staticmethod
    def send_appointment_confirmation(appointment):
        """Send confirmation email when appointment is created"""
        try:
            subject = f'Pickup Request Confirmed - #{appointment.id}'
            
            html_message = render_to_string('emails/appointment_confirmation.html', {
                'appointment': appointment,
                'user': appointment.customer
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[appointment.customer.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Confirmation email sent for appointment {appointment.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send confirmation email for appointment {appointment.id}: {str(e)}")
            return False
    
    @staticmethod
    def send_status_update(appointment, previous_status):
        """Send email when appointment status changes"""
        try:
            subject = f'Pickup Status Update - #{appointment.id}'
            
            html_message = render_to_string('emails/status_update.html', {
                'appointment': appointment,
                'previous_status': previous_status,
                'user': appointment.customer
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[appointment.customer.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Status update email sent for appointment {appointment.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send status update email for appointment {appointment.id}: {str(e)}")
            return False
    
    @staticmethod
    def send_pickup_reminder(appointment):
        """Send reminder email 24 hours before pickup"""
        try:
            subject = f'Pickup Reminder - Tomorrow at {appointment.preferred_time}'
            
            html_message = render_to_string('emails/pickup_reminder.html', {
                'appointment': appointment,
                'user': appointment.customer
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[appointment.customer.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Reminder email sent for appointment {appointment.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send reminder email for appointment {appointment.id}: {str(e)}")
            return False


class SecurityUtils:
    """Utility functions for security enhancements"""
    
    @staticmethod
    def log_user_action(user, action, details=None):
        """Log user actions for audit trail"""
        logger.info(f"User {user.username} ({user.id}) performed action: {action}. Details: {details}")
    
    @staticmethod
    def is_safe_redirect_url(url, allowed_hosts=None):
        """Check if redirect URL is safe to prevent open redirect attacks"""
        if not url:
            return False
        
        if allowed_hosts is None:
            allowed_hosts = settings.ALLOWED_HOSTS
        
        # Simple validation - in production, use django.utils.http.url_has_allowed_host_and_scheme
        return url.startswith('/') and not url.startswith('//')
    
    @staticmethod
    def sanitize_user_input(text):
        """Basic input sanitization"""
        if not text:
            return text
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<script', '</script', 'javascript:', 'data:', 'vbscript:']
        text_lower = text.lower()
        
        for char in dangerous_chars:
            if char in text_lower:
                text = text.replace(char, '')
        
        return text.strip()


def is_staff_like(user):
    """Check if user has staff-like permissions (staff, admin, or superuser)"""
    if not user or not user.is_authenticated:
        return False
    
    return (
        user.is_staff or 
        user.is_superuser or 
        (hasattr(user, 'role') and user.role in ['staff', 'admin'])
    )


def send_email_notification(appointment, notification_type='confirmation'):
    """Legacy function for backward compatibility"""
    if notification_type == 'confirmation':
        return EmailService.send_appointment_confirmation(appointment)
    elif notification_type == 'status_update':
        return EmailService.send_status_update(appointment, None)
    elif notification_type == 'reminder':
        return EmailService.send_pickup_reminder(appointment)
    return False


def create_logs_directory():
    """Create logs directory if it doesn't exist"""
    import os
    logs_dir = settings.BASE_DIR / 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        logger.info("Created logs directory")
