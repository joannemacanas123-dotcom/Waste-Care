from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Count
import json

from .models import Appointment, Notification, User
from .analytics import WasteCareAnalytics

@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)

@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """Mark all notifications as read for the current user"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})

@login_required
def get_appointment_stats(request):
    """Get real-time appointment statistics"""
    analytics = WasteCareAnalytics()
    stats = analytics.get_dashboard_stats(request.user)
    return JsonResponse(stats)

@login_required
def search_appointments_api(request):
    """API endpoint for appointment search with autocomplete"""
    query = request.GET.get('q', '')
    
    if request.user.role == 'residents':
        appointments = Appointment.objects.filter(customer=request.user)
    else:
        appointments = Appointment.objects.all()
    
    if query:
        appointments = appointments.filter(
            Q(address__icontains=query) |
            Q(notes__icontains=query) |
            Q(waste_type__icontains=query)
        )[:10]
    
    results = []
    for apt in appointments:
        results.append({
            'id': apt.id,
            'address': apt.address,
            'waste_type': apt.get_waste_type_display(),
            'date': apt.preferred_date.isoformat(),
            'status': apt.get_status_display(),
            'url': f'/appointments/{apt.id}/'
        })
    
    return JsonResponse({'results': results})

@login_required
def get_available_time_slots(request):
    """Get available time slots for a specific date"""
    date_str = request.GET.get('date')
    waste_type = request.GET.get('waste_type', 'general')
    
    if not date_str:
        return JsonResponse({'error': 'Date parameter required'}, status=400)
    
    try:
        from datetime import datetime
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get existing appointments for the date
        existing_appointments = Appointment.objects.filter(
            preferred_date=date,
            status__in=['scheduled', 'in_progress']
        ).values_list('preferred_time', flat=True)
        
        # Define time slots with capacity
        time_slots = [
            {'time': '08:00', 'capacity': 5, 'waste_types': ['general', 'recyclable', 'organic']},
            {'time': '10:00', 'capacity': 8, 'waste_types': ['all']},
            {'time': '12:00', 'capacity': 6, 'waste_types': ['general', 'recyclable']},
            {'time': '14:00', 'capacity': 8, 'waste_types': ['all']},
            {'time': '16:00', 'capacity': 5, 'waste_types': ['general', 'bulk']},
        ]
        
        available_slots = []
        for slot in time_slots:
            # Count existing appointments for this time slot
            slot_time = datetime.strptime(slot['time'], '%H:%M').time()
            current_bookings = list(existing_appointments).count(slot_time)
            
            # Check if waste type is allowed
            if waste_type in slot['waste_types'] or 'all' in slot['waste_types']:
                available_capacity = slot['capacity'] - current_bookings
                if available_capacity > 0:
                    load_level = 'low' if available_capacity > 3 else 'medium' if available_capacity > 1 else 'high'
                    available_slots.append({
                        'time': slot['time'],
                        'available_capacity': available_capacity,
                        'load_level': load_level,
                        'recommended': load_level == 'low'
                    })
        
        return JsonResponse({'available_slots': available_slots})
        
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

@login_required
def update_appointment_status(request, appointment_id):
    """Update appointment status via API"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        
        # Check permissions
        if request.user.role == 'residents' and appointment.customer != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status not in dict(Appointment.STATUS_CHOICES):
            return JsonResponse({'error': 'Invalid status'}, status=400)
        
        old_status = appointment.status
        appointment.status = new_status
        
        # Update timestamps based on status
        if new_status == 'in_progress' and old_status != 'in_progress':
            appointment.scheduled_datetime = timezone.now()
        elif new_status == 'completed' and old_status != 'completed':
            appointment.completion_datetime = timezone.now()
        
        appointment.save()
        
        # Create notification for customer
        if appointment.customer != request.user:
            Notification.objects.create(
                user=appointment.customer,
                title=f"Appointment Status Updated",
                message=f"Your {appointment.waste_type} pickup status changed to {appointment.get_status_display()}"
            )
        
        return JsonResponse({
            'status': 'success',
            'new_status': appointment.get_status_display(),
            'updated_at': appointment.updated_at.isoformat()
        })
        
    except Appointment.DoesNotExist:
        return JsonResponse({'error': 'Appointment not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

@login_required
def get_route_optimization(request):
    """Get optimized route for drivers"""
    if request.user.role not in ['driver', 'staff', 'admin']:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    date_str = request.GET.get('date', timezone.now().date().isoformat())
    
    try:
        from datetime import datetime
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get appointments for the date
        appointments = Appointment.objects.filter(
            preferred_date=date,
            status__in=['scheduled', 'in_progress']
        ).select_related('customer')
        
        if request.user.role == 'driver':
            appointments = appointments.filter(handled_by=request.user)
        
        # Simple route optimization (in real app, use Google Maps API or similar)
        route_data = []
        for apt in appointments:
            route_data.append({
                'id': apt.id,
                'address': apt.address,
                'customer': apt.customer.get_full_name() or apt.customer.username,
                'waste_type': apt.get_waste_type_display(),
                'time': apt.preferred_time.strftime('%H:%M'),
                'status': apt.status,
                'priority': apt.priority,
                'estimated_duration': 15,  # minutes
                'coordinates': {
                    'lat': 0,  # Would be populated from geocoding
                    'lng': 0
                }
            })
        
        # Sort by priority and time
        route_data.sort(key=lambda x: (x['priority'] != 'urgent', x['time']))
        
        return JsonResponse({
            'route': route_data,
            'total_stops': len(route_data),
            'estimated_duration': len(route_data) * 15,  # Simple calculation
            'optimized': True
        })
        
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

@login_required
def get_appointment_details(request, appointment_id):
    """Get detailed appointment information for calendar modal"""
    try:
        appointment = Appointment.objects.select_related('customer').get(id=appointment_id)
        
        # Check permissions
        if request.user.role == 'residents' and appointment.customer != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        return JsonResponse({
            'id': appointment.id,
            'customer_name': appointment.customer.get_full_name() or appointment.customer.username,
            'waste_type': appointment.waste_type,
            'waste_type_display': appointment.get_waste_type_display(),
            'status': appointment.status,
            'status_display': appointment.get_status_display(),
            'preferred_date': appointment.preferred_date.isoformat(),
            'preferred_time': appointment.preferred_time.strftime('%H:%M'),
            'address': appointment.address,
            'priority': appointment.priority,
            'priority_display': appointment.get_priority_display(),
            'estimated_weight': float(appointment.estimated_weight) if appointment.estimated_weight else None,
            'notes': appointment.notes,
            'special_instructions': appointment.special_instructions,
            'created_at': appointment.created_at.isoformat(),
        })
        
    except Appointment.DoesNotExist:
        return JsonResponse({'error': 'Appointment not found'}, status=404)

@login_required
def get_map_appointments(request):
    """Get appointments with location data for map display"""
    # Filter appointments based on user role
    if request.user.role == 'residents':
        appointments = Appointment.objects.filter(customer=request.user)
    else:
        appointments = Appointment.objects.all()
    
    # Apply status filter if provided
    status_filter = request.GET.get('status')
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    # Apply date filter if provided
    date_filter = request.GET.get('date')
    if date_filter:
        appointments = appointments.filter(preferred_date=date_filter)
    
    # Only include appointments with location data
    appointments = appointments.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    
    # Build map data
    map_data = []
    for apt in appointments.select_related('customer'):
        # Determine marker color based on status
        status_colors = {
            'requested': '#FFA500',  # Orange
            'scheduled': '#4A90E2',  # Blue
            'in_progress': '#FFD700',  # Gold
            'completed': '#28A745',  # Green
            'cancelled': '#DC3545',  # Red
        }
        
        map_data.append({
            'id': apt.id,
            'address': apt.address,
            'latitude': float(apt.latitude),
            'longitude': float(apt.longitude),
            'waste_type': apt.get_waste_type_display(),
            'status': apt.status,
            'status_display': apt.get_status_display(),
            'priority': apt.priority,
            'priority_display': apt.get_priority_display(),
            'preferred_date': apt.preferred_date.isoformat(),
            'preferred_time': apt.preferred_time.strftime('%H:%M'),
            'customer_name': apt.customer.get_full_name() or apt.customer.username,
            'estimated_weight': float(apt.estimated_weight) if apt.estimated_weight else None,
            'marker_color': status_colors.get(apt.status, '#6C757D'),
            'notes': apt.notes[:100] if apt.notes else '',
        })
    
    return JsonResponse({
        'appointments': map_data,
        'total': len(map_data)
    })