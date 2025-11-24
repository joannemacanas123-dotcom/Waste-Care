from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = [
        ("residents", "Residents"),
        ("staff", "Staff"),
        ("admin", "Admin"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="residents")

    def is_staff_like(self) -> bool:
        return self.role in {"staff", "admin"} or super().is_staff


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50)
    price_per_month = models.DecimalField(max_digits=6, decimal_places=2)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    
    WASTE_TYPE_CHOICES = [
        ("general", "General Waste"),
        ("recyclable", "Recyclable"),
        ("organic", "Organic/Compost"),
        ("hazardous", "Hazardous Waste"),
        ("bulk", "Bulk Items"),
    ]
    
    PRIORITY_CHOICES = [
        ("low", "Low Priority"),
        ("normal", "Normal"),
        ("high", "High Priority"),
        ("urgent", "Urgent"),
    ]
    
    DAY_CHOICES = [
        ("monday", "Monday"),
        ("tuesday", "Tuesday"),
        ("wednesday", "Wednesday"),
        ("thursday", "Thursday"),
        ("friday", "Friday"),
        ("saturday", "Saturday"),
        ("sunday", "Sunday"),
    ]
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="appointments")
    pickup_day = models.CharField(max_length=10, choices=DAY_CHOICES, default="monday", help_text="Preferred day of the week for pickup")
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Latitude coordinate")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Longitude coordinate")
    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    waste_type = models.CharField(max_length=20, choices=WASTE_TYPE_CHOICES, default="general")
    estimated_weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Weight in kg")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="normal")
    notes = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True, help_text="Special handling requirements")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    handled_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="handled_appointments"
    )
    scheduled_datetime = models.DateTimeField(null=True, blank=True)
    completion_datetime = models.DateTimeField(null=True, blank=True)
    actual_weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'preferred_date']),
            models.Index(fields=['customer', 'status']),
        ]

    def __str__(self):
        return f"{self.customer.username} - {self.preferred_date} {self.status}"


class ServiceHistory(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name="service_history")
    completed_at = models.DateTimeField(default=timezone.now)
    staff_notes = models.TextField(blank=True)

    def __str__(self):
        return f"History for {self.appointment.id}"


class AppointmentHistory(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="history_logs")
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    changes = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.appointment.id} - {self.action} at {self.timestamp}"


class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class JournalEntry(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="journals")
    title = models.CharField(max_length=120)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.username} - {self.title}"


class Feedback(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="feedbacks")
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name="feedbacks")
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], help_text="Rating from 1 to 5 stars")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer.username} - {self.rating} stars"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('confirmation', 'Pickup Confirmation'),
        ('approval', 'Appointment Approval'),
        ('cancellation', 'Cancellation'),
        ('reminder', 'Reminder'),
        ('announcement', 'Admin Announcement'),
        ('update', 'General Update'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='update')
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']

    @staticmethod
    def notify_pickup_completed(appointment: Appointment):
        Notification.objects.create(
            user=appointment.customer,
            message=f"Your pickup was completed on {timezone.now().strftime('%b %d, %Y at %I:%M %p')}. Waste type: {appointment.get_waste_type_display()}.",
            notification_type='confirmation',
            appointment=appointment
        )
    
    @staticmethod
    def notify_appointment_approved(appointment: Appointment):
        Notification.objects.create(
            user=appointment.customer,
            message=f"Your appointment for {appointment.preferred_date.strftime('%b %d, %Y')} at {appointment.preferred_time.strftime('%I:%M %p')} has been approved. Waste type: {appointment.get_waste_type_display()}.",
            notification_type='approval',
            appointment=appointment
        )
    
    @staticmethod
    def notify_appointment_cancelled(appointment: Appointment, reason=''):
        msg = f"Your appointment for {appointment.preferred_date.strftime('%b %d, %Y')} has been cancelled."
        if reason:
            msg += f" Reason: {reason}"
        Notification.objects.create(
            user=appointment.customer,
            message=msg,
            notification_type='cancellation',
            appointment=appointment
        )
    
    @staticmethod
    def notify_pickup_reminder(appointment: Appointment):
        Notification.objects.create(
            user=appointment.customer,
            message=f"Reminder: Your scheduled pickup is tomorrow ({appointment.preferred_date.strftime('%b %d, %Y')}) at {appointment.preferred_time.strftime('%I:%M %p')}. Waste type: {appointment.get_waste_type_display()}.",
            notification_type='reminder',
            appointment=appointment
        )
    
    @staticmethod
    def create_announcement(message: str, users=None):
        if users is None:
            users = User.objects.filter(role='residents')
        for user in users:
            Notification.objects.create(
                user=user,
                message=f"Admin announcement: {message}",
                notification_type='announcement'
            )

# Create your models here.
