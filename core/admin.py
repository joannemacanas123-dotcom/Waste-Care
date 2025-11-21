from django.contrib import admin
from django.db.models import Count, Q
from django.utils.html import format_html
from .models import User, Appointment, ServiceHistory, Article, JournalEntry, Feedback, SubscriptionPlan, Notification, AppointmentHistory


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "role", "is_active", "date_joined", "appointment_count")
    list_filter = ("role", "is_active", "date_joined")
    search_fields = ("username", "email", "first_name", "last_name")
    actions = ["activate_users", "deactivate_users"]
    
    def appointment_count(self, obj):
        return obj.appointments.count()
    appointment_count.short_description = "Appointments"
    
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_users.short_description = "Deactivate selected users"


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "address_short", "preferred_date", "preferred_time", "status_badge", "waste_type", "priority", "handled_by", "created_at")
    list_filter = ("status", "waste_type", "priority", "pickup_day", "preferred_date", "created_at")
    search_fields = ("customer__username", "address", "notes", "special_instructions")
    readonly_fields = ("created_at", "updated_at")
    actions = ["mark_scheduled", "mark_in_progress", "mark_completed", "mark_cancelled"]
    date_hierarchy = "preferred_date"
    
    def address_short(self, obj):
        return obj.address[:30] + "..." if len(obj.address) > 30 else obj.address
    address_short.short_description = "Address"
    
    def status_badge(self, obj):
        colors = {
            "requested": "orange",
            "scheduled": "blue",
            "in_progress": "gold",
            "completed": "green",
            "cancelled": "red"
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, "gray"),
            obj.get_status_display()
        )
    status_badge.short_description = "Status"
    
    def mark_scheduled(self, request, queryset):
        queryset.update(status="scheduled")
    mark_scheduled.short_description = "Mark as Scheduled"
    
    def mark_in_progress(self, request, queryset):
        queryset.update(status="in_progress")
    mark_in_progress.short_description = "Mark as In Progress"
    
    def mark_completed(self, request, queryset):
        queryset.update(status="completed")
    mark_completed.short_description = "Mark as Completed"
    
    def mark_cancelled(self, request, queryset):
        queryset.update(status="cancelled")
    mark_cancelled.short_description = "Mark as Cancelled"


@admin.register(ServiceHistory)
class ServiceHistoryAdmin(admin.ModelAdmin):
    list_display = ("appointment", "completed_at", "staff_notes_short")
    search_fields = ("appointment__customer__username", "staff_notes")
    date_hierarchy = "completed_at"
    
    def staff_notes_short(self, obj):
        return obj.staff_notes[:50] + "..." if len(obj.staff_notes) > 50 else obj.staff_notes
    staff_notes_short.short_description = "Notes"


@admin.register(AppointmentHistory)
class AppointmentHistoryAdmin(admin.ModelAdmin):
    list_display = ("appointment", "action", "changed_by", "timestamp", "changes_short")
    list_filter = ("action", "timestamp")
    search_fields = ("appointment__customer__username", "changes")
    readonly_fields = ("appointment", "changed_by", "action", "changes", "timestamp")
    date_hierarchy = "timestamp"
    
    def changes_short(self, obj):
        return obj.changes[:50] + "..." if len(obj.changes) > 50 else obj.changes
    changes_short.short_description = "Changes"


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("customer", "message_short", "created_at")
    search_fields = ("customer__username", "message")
    date_hierarchy = "created_at"
    
    def message_short(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_short.short_description = "Message"


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "published", "created_at")


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ("customer", "title", "created_at")


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price_per_month", "is_active")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "created_at", "is_read")
    list_filter = ("is_read", "created_at")
    actions = ["mark_as_read"]
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Mark as read"
