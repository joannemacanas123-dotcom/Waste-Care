from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from .models import Appointment, User, Feedback, ServiceHistory
import json

class WasteCareAnalytics:
    """Advanced analytics for Waste Care application"""
    
    @staticmethod
    def get_dashboard_stats(user=None):
        """Get comprehensive dashboard statistics"""
        if user and user.role == 'customer':
            # Customer-specific stats
            appointments = Appointment.objects.filter(customer=user)
        else:
            # Staff/Admin stats
            appointments = Appointment.objects.all()
        
        total_appointments = appointments.count()
        completed_appointments = appointments.filter(status='completed').count()
        pending_appointments = appointments.filter(status__in=['requested', 'scheduled']).count()
        
        # Calculate completion rate
        completion_rate = (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0
        
        # Get waste type distribution
        waste_types = appointments.values('waste_type').annotate(count=Count('waste_type'))
        
        # Monthly trend data
        monthly_data = WasteCareAnalytics.get_monthly_trends(user)
        
        return {
            'total_appointments': total_appointments,
            'completed_appointments': completed_appointments,
            'pending_appointments': pending_appointments,
            'completion_rate': round(completion_rate, 1),
            'waste_types': list(waste_types),
            'monthly_trends': monthly_data,
        }
    
    @staticmethod
    def get_monthly_trends(user=None):
        """Get monthly appointment trends for charts"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=180)  # 6 months
        
        if user and user.role == 'customer':
            appointments = Appointment.objects.filter(customer=user, created_at__date__gte=start_date)
        else:
            appointments = Appointment.objects.filter(created_at__date__gte=start_date)
        
        # Group by month
        monthly_counts = {}
        for appointment in appointments:
            month_key = appointment.created_at.strftime('%Y-%m')
            monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
        
        return monthly_counts
    
    @staticmethod
    def get_performance_metrics():
        """Get system performance metrics"""
        total_users = User.objects.count()
        active_users = User.objects.filter(appointments__created_at__gte=timezone.now() - timedelta(days=30)).distinct().count()
        
        avg_completion_time = ServiceHistory.objects.aggregate(
            avg_time=Avg('completed_at')
        )
        
        customer_satisfaction = Feedback.objects.aggregate(
            avg_rating=Avg('rating')
        ) if hasattr(Feedback, 'rating') else {'avg_rating': None}
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'user_engagement': round((active_users / total_users * 100), 1) if total_users > 0 else 0,
            'customer_satisfaction': customer_satisfaction['avg_rating']
        }
