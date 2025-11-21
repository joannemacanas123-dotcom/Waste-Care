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
        ("requested", "Requested"),
        ("scheduled", "Scheduled"),
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="requested")
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
        return f"History for {self.appointment_id}"


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
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    @staticmethod
    def notify_pickup_completed(appointment: Appointment):
        Notification.objects.create(
            user=appointment.customer,
            message=f"Your trash was picked up on {timezone.now().strftime('%Y-%m-%d %H:%M')}.",
        )

# Create your models here.
