from django.contrib import admin
from .models import User, Appointment, ServiceHistory, Article, JournalEntry, Feedback, SubscriptionPlan, Notification


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "role", "is_active")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("customer", "preferred_date", "preferred_time", "status", "handled_by", "created_at")
    list_filter = ("status", "preferred_date")
    search_fields = ("customer__username", "address", "notes")


@admin.register(ServiceHistory)
class ServiceHistoryAdmin(admin.ModelAdmin):
    list_display = ("appointment", "completed_at")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "published", "created_at")


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ("customer", "title", "created_at")


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("customer", "created_at")


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price_per_month", "is_active")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "created_at", "is_read")
