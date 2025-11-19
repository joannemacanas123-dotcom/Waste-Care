from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import Appointment, User, Notification, Article, Feedback
from .analytics import WasteCareAnalytics
from .forms import AppointmentForm, FeedbackForm

@login_required
def advanced_dashboard(request):
    """Enhanced dashboard with analytics and insights"""
    analytics = WasteCareAnalytics()
    stats = analytics.get_dashboard_stats(request.user)
    
    # Get recent activity
    recent_appointments = Appointment.objects.filter(
        customer=request.user if request.user.role == 'customer' else None
    ).order_by('-created_at')[:5]
    
    # Get upcoming appointments
    upcoming = Appointment.objects.filter(
        customer=request.user if request.user.role == 'customer' else None,
        preferred_date__gte=timezone.now().date(),
        status__in=['requested', 'scheduled']
    ).order_by('preferred_date')[:3]
    
    # Get unread notifications
    notifications = Notification.objects.filter(
        user=request.user, 
        is_read=False
    ).order_by('-created_at')[:5]
    
    context = {
        'stats': stats,
        'recent_appointments': recent_appointments,
        'upcoming_appointments': upcoming,
        'notifications': notifications,
        'chart_data': json.dumps(stats['monthly_trends']),
        'waste_type_data': json.dumps(stats['waste_types']),
    }
    
    return render(request, 'core/advanced_dashboard.html', context)

@login_required
def appointment_calendar(request):
    """Calendar view for appointments"""
    # Get appointments for calendar
    if request.user.role == 'customer':
        appointments = Appointment.objects.filter(customer=request.user)
    else:
        appointments = Appointment.objects.all()
    
    # Format for calendar
    calendar_events = []
    for apt in appointments:
        calendar_events.append({
            'id': apt.id,
            'title': f"{apt.waste_type.title()} - {apt.customer.username}",
            'start': apt.preferred_date.isoformat(),
            'backgroundColor': {
                'requested': '#ffc107',
                'scheduled': '#17a2b8',
                'in_progress': '#fd7e14',
                'completed': '#28a745',
                'cancelled': '#dc3545'
            }.get(apt.status, '#6c757d'),
            'status': apt.status,
            'waste_type': apt.waste_type,
        })
    
    context = {
        'calendar_events': json.dumps(calendar_events),
    }
    
    return render(request, 'core/appointment_calendar.html', context)

@login_required
def smart_scheduling(request):
    """AI-powered smart scheduling suggestions"""
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.customer = request.user
            
            # Smart scheduling logic
            suggested_times = get_optimal_time_slots(
                appointment.preferred_date,
                appointment.waste_type,
                appointment.address
            )
            
            if suggested_times:
                appointment.preferred_time = suggested_times[0]
            
            appointment.save()
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                title="Pickup Scheduled",
                message=f"Your {appointment.waste_type} pickup has been scheduled for {appointment.preferred_date}"
            )
            
            messages.success(request, 'Pickup scheduled with optimal time slot!')
            return redirect('core:dashboard')
    else:
        form = AppointmentForm()
    
    # Get scheduling insights
    busy_dates = get_busy_dates()
    recommended_times = get_recommended_times()
    
    context = {
        'form': form,
        'busy_dates': json.dumps(busy_dates),
        'recommended_times': recommended_times,
    }
    
    return render(request, 'core/smart_scheduling.html', context)

def get_optimal_time_slots(date, waste_type, address):
    """Calculate optimal time slots based on various factors"""
    # Get existing appointments for the date
    existing_appointments = Appointment.objects.filter(
        preferred_date=date,
        status__in=['scheduled', 'in_progress']
    ).values_list('preferred_time', flat=True)
    
    # Define available time slots
    time_slots = [
        datetime.strptime('08:00', '%H:%M').time(),
        datetime.strptime('10:00', '%H:%M').time(),
        datetime.strptime('12:00', '%H:%M').time(),
        datetime.strptime('14:00', '%H:%M').time(),
        datetime.strptime('16:00', '%H:%M').time(),
    ]
    
    # Filter out busy slots
    available_slots = [slot for slot in time_slots if slot not in existing_appointments]
    
    # Prioritize based on waste type
    if waste_type == 'organic':
        # Morning slots preferred for organic waste
        available_slots.sort()
    elif waste_type == 'hazardous':
        # Specific time slots for hazardous waste
        available_slots = [slot for slot in available_slots if slot.hour in [10, 14]]
    
    return available_slots

def get_busy_dates():
    """Get dates with high appointment density"""
    from django.db.models import Count
    
    busy_dates = Appointment.objects.filter(
        preferred_date__gte=timezone.now().date()
    ).values('preferred_date').annotate(
        count=Count('id')
    ).filter(count__gte=5).values_list('preferred_date', flat=True)
    
    return [date.isoformat() for date in busy_dates]

def get_recommended_times():
    """Get recommended time slots based on historical data"""
    return [
        {'time': '08:00', 'load': 'low', 'recommended': True},
        {'time': '10:00', 'load': 'medium', 'recommended': True},
        {'time': '12:00', 'load': 'high', 'recommended': False},
        {'time': '14:00', 'load': 'medium', 'recommended': True},
        {'time': '16:00', 'load': 'low', 'recommended': True},
    ]

@login_required
def appointment_search(request):
    """Advanced appointment search and filtering"""
    appointments = Appointment.objects.all()
    
    if request.user.role == 'customer':
        appointments = appointments.filter(customer=request.user)
    
    # Apply filters
    status_filter = request.GET.get('status')
    waste_type_filter = request.GET.get('waste_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search_query = request.GET.get('q')
    
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    if waste_type_filter:
        appointments = appointments.filter(waste_type=waste_type_filter)
    
    if date_from:
        appointments = appointments.filter(preferred_date__gte=date_from)
    
    if date_to:
        appointments = appointments.filter(preferred_date__lte=date_to)
    
    if search_query:
        appointments = appointments.filter(
            Q(address__icontains=search_query) |
            Q(notes__icontains=search_query) |
            Q(customer__username__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(appointments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': Appointment.STATUS_CHOICES,
        'waste_type_choices': Appointment.WASTE_TYPE_CHOICES,
        'current_filters': {
            'status': status_filter,
            'waste_type': waste_type_filter,
            'date_from': date_from,
            'date_to': date_to,
            'q': search_query,
        }
    }
    
    return render(request, 'core/appointment_search.html', context)

@login_required
def pickup_map(request):
    """Interactive map view for tracking garbage pickup locations"""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    
    context = {
        'status_choices': Appointment.STATUS_CHOICES,
        'status_filter': status_filter,
        'date_filter': date_filter,
    }
    
    return render(request, 'core/pickup_map.html', context)
