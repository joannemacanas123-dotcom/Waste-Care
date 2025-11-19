from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.core.exceptions import PermissionDenied
from django import forms
from django.db.models import Count
from datetime import datetime, timedelta
import json
import logging

from .models import User, Appointment, Article, JournalEntry, Feedback, SubscriptionPlan, Notification, ServiceHistory
from .forms import AppointmentForm, AppointmentStatusForm, LoginForm, RegisterForm, UserProfileForm
from .utils import EmailService, SecurityUtils, is_staff_like

logger = logging.getLogger(__name__)


def home(request):
    """
    Homepage view with welcome content and key statistics
    """
    # Get some basic statistics for the homepage
    context = {
        'total_appointments': Appointment.objects.count(),
        'completed_appointments': Appointment.objects.filter(status='completed').count(),
        'active_users': User.objects.filter(is_active=True).count(),
    }
    return render(request, "core/home.html", context)


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("username", "email", "role")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            raise forms.ValidationError("Passwords do not match")
        return cleaned


def is_staff_like(user: User) -> bool:
    return user.is_authenticated and (user.role in {"staff", "admin"} or user.is_staff)


@ensure_csrf_cookie
@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user:
            login(request, user)
            return redirect("core:dashboard")
        messages.error(request, "Invalid credentials")
    return render(request, "core/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("core:login")


@ensure_csrf_cookie
@csrf_protect
def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = User.objects.create_user(
            username=form.cleaned_data["username"],
            email=form.cleaned_data.get("email"),
            password=form.cleaned_data["password1"],
            role=form.cleaned_data.get("role", "customer"),
        )
        login(request, user)
        return redirect("core:dashboard")
    return render(request, "core/register.html", {"form": form})


@login_required
def dashboard(request):
    from django.db.models import Count
    from datetime import datetime, timedelta
    import json
    
    if is_staff_like(request.user):
        appointments = Appointment.objects.order_by("-created_at")[:5]
        feedbacks = Feedback.objects.order_by("-created_at")[:5]
        total_appointments = Appointment.objects.count()
        pending_appointments = Appointment.objects.filter(status__in=['requested', 'scheduled']).count()
        completed_appointments = Appointment.objects.filter(status='completed').count()
    else:
        appointments = Appointment.objects.filter(customer=request.user).order_by("-created_at")[:5]
        feedbacks = Feedback.objects.filter(customer=request.user).order_by("-created_at")[:5]
        total_appointments = Appointment.objects.filter(customer=request.user).count()
        pending_appointments = Appointment.objects.filter(customer=request.user, status__in=['requested', 'scheduled']).count()
        completed_appointments = Appointment.objects.filter(customer=request.user, status='completed').count()
    
    # Get recent notifications
    recent_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:3]
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    
    # Generate chart data for the last 7 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6)
    
    chart_labels = []
    chart_data = []
    
    for i in range(7):
        date = start_date + timedelta(days=i)
        chart_labels.append(date.strftime('%a'))
        
        if is_staff_like(request.user):
            count = Appointment.objects.filter(created_at__date=date).count()
        else:
            count = Appointment.objects.filter(customer=request.user, created_at__date=date).count()
        chart_data.append(count)
    
    # Status distribution data
    if is_staff_like(request.user):
        status_counts = Appointment.objects.values('status').annotate(count=Count('status'))
    else:
        status_counts = Appointment.objects.filter(customer=request.user).values('status').annotate(count=Count('status'))
    
    status_labels = []
    status_data = []
    for item in status_counts:
        status_labels.append(dict(Appointment.STATUS_CHOICES).get(item['status'], item['status']))
        status_data.append(item['count'])
    
    context = {
        "appointments": appointments,
        "feedbacks": feedbacks,
        "total_appointments": total_appointments,
        "pending_appointments": pending_appointments,
        "completed_appointments": completed_appointments,
        "recent_notifications": recent_notifications,
        "unread_notifications": unread_notifications,
        "chart_labels": json.dumps(chart_labels),
        "chart_data": json.dumps(chart_data),
        "status_labels": json.dumps(status_labels),
        "status_data": json.dumps(status_data),
    }
    
    return render(request, "core/dashboard.html", context)


@login_required
def pickup_list(request):
    from django.db.models import Q
    
    if is_staff_like(request.user):
        qs = Appointment.objects.all()
    else:
        qs = Appointment.objects.filter(customer=request.user)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        qs = qs.filter(
            Q(address__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)
    
    # Date filter
    date_from = request.GET.get('date_from')
    if date_from:
        qs = qs.filter(preferred_date__gte=date_from)
    
    return render(request, "core/pickup_list.html", {"appointments": qs.order_by("-created_at")})


@login_required
def pickup_create(request):
    form = AppointmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        appt = form.save(commit=False)
        appt.customer = request.user
        appt.save()
        
        # Log user action
        SecurityUtils.log_user_action(request.user, "Created pickup request", f"Appointment ID: {appt.id}")
        
        # Send confirmation email
        if request.user.email:
            EmailService.send_appointment_confirmation(appt)
        
        # Create notification
        Notification.objects.create(
            user=request.user,
            message=f"Your pickup request #{appt.id} has been submitted and is pending review."
        )
        
        messages.success(request, "Pickup request submitted successfully! You'll receive a confirmation email shortly.")
        return redirect("core:pickup_list")
    return render(request, "core/pickup_form.html", {"form": form})


@login_required
def pickup_detail(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    
    # Security check: users can only view their own appointments unless they're staff
    if not (is_staff_like(request.user) or appt.customer == request.user):
        logger.warning(f"User {request.user.username} attempted to access appointment {pk} without permission")
        raise PermissionDenied("You don't have permission to view this appointment.")
    
    # Log access for audit trail
    SecurityUtils.log_user_action(request.user, "Viewed appointment details", f"Appointment ID: {appt.id}")
    
    return render(request, "core/pickup_detail.html", {"appointment": appt})


@login_required
def pickup_update(request, pk):
    try:
        appt = Appointment.objects.get(pk=pk)
        
        # Security check: users can only edit their own appointments unless they're staff
        if not (is_staff_like(request.user) or appt.customer == request.user):
            messages.error(request, "You don't have permission to edit this appointment.")
            return redirect("core:pickup_list")
    except Appointment.DoesNotExist:
        messages.error(request, "Appointment not found.")
        return redirect("core:pickup_list")
    
    # Security check: only allow editing if status allows it
    if appt.status not in ['requested', 'scheduled']:
        messages.error(request, "This appointment cannot be modified in its current status.")
        return redirect("core:pickup_detail", pk=pk)
    
    form = AppointmentForm(request.POST or None, instance=appt)
    if request.method == "POST" and form.is_valid():
        form.save()
        
        # Log user action
        SecurityUtils.log_user_action(request.user, "Updated pickup request", f"Appointment ID: {appt.id}")
        
        # Create notification
        Notification.objects.create(
            user=request.user,
            message=f"Your pickup request #{appt.id} has been updated."
        )
        
        messages.success(request, "Appointment updated successfully.")
        return redirect("core:pickup_detail", pk=pk)
    return render(request, "core/pickup_form.html", {"form": form})


@login_required
def pickup_delete(request, pk):
    try:
        appt = Appointment.objects.get(pk=pk)
        
        # Security check: users can only delete their own appointments unless they're staff
        if not (is_staff_like(request.user) or appt.customer == request.user):
            messages.error(request, "You don't have permission to delete this appointment.")
            return redirect("core:pickup_list")
    except Appointment.DoesNotExist:
        messages.error(request, "Appointment not found.")
        return redirect("core:pickup_list")
    
    if request.method == "POST":
        appt.delete()
        messages.success(request, "Appointment deleted.")
        return redirect("core:pickup_list")
    return render(request, "core/pickup_detail.html", {"appointment": appt, "confirm_delete": True})


@login_required
@user_passes_test(is_staff_like)
def pickup_status_update(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)
    form = AppointmentStatusForm(request.POST or None, instance=appt)
    if request.method == "POST" and form.is_valid():
        previous_status = appt.status
        appt = form.save(commit=False)
        
        if appt.status == "completed" and previous_status != "completed":
            appt.updated_at = timezone.now()
        
        appt.handled_by = request.user if appt.status != 'requested' else None
        appt.save()
        
        # Log staff action
        SecurityUtils.log_user_action(
            request.user, 
            "Updated appointment status", 
            f"Appointment ID: {appt.id}, Status: {previous_status} -> {appt.status}"
        )
        
        # Send status update email
        if appt.customer.email and previous_status != appt.status:
            EmailService.send_status_update(appt, previous_status)
        
        # Handle completion
        if appt.status == "completed" and not hasattr(appt, "service_history"):
            ServiceHistory.objects.create(
                appointment=appt, 
                completed_at=timezone.now(),
                staff_notes=f"Completed by {request.user.username}"
            )
            Notification.notify_pickup_completed(appt)
            messages.success(request, "Marked completed. Customer notified via email and in-app notification.")
        else:
            # Create notification for status change
            Notification.objects.create(
                user=appt.customer,
                message=f"Your pickup request #{appt.id} status has been updated to {appt.get_status_display()}."
            )
            messages.success(request, "Status updated successfully. Customer has been notified.")
        
        return redirect("core:pickup_detail", pk=pk)
    return render(request, "core/pickup_form.html", {"form": form, "is_status": True})


@login_required
def history_view(request):
    if is_staff_like(request.user):
        qs = ServiceHistory.objects.select_related("appointment").order_by("-completed_at")
    else:
        qs = ServiceHistory.objects.select_related("appointment").filter(
            appointment__customer=request.user
        ).order_by("-completed_at")
    return render(request, "core/history.html", {"history": qs})


@login_required
def notifications(request):
    notes = Notification.objects.filter(user=request.user).order_by("-created_at")
    # Mark all as read when viewing
    if request.method == 'POST' and 'mark_all_read' in request.POST:
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, "All notifications marked as read.")
        return redirect('core:notifications')
    
    return render(request, "core/notifications.html", {"notifications": notes})


@login_required
def notification_mark_read(request, pk):
    note = get_object_or_404(Notification, pk=pk, user=request.user)
    note.is_read = True
    note.save()
    messages.success(request, "Notification marked as read.")
    return redirect("core:notifications")


@login_required
def profile_view(request):
    """View user profile"""
    return render(request, "core/profile.html", {"user": request.user})


@login_required
def settings_view(request):
    """View and update user settings"""
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("core:profile")
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, "core/settings.html", {"form": form})
