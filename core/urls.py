from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, advanced_views, api_views

app_name = 'core'

urlpatterns = [
    # Homepage and Dashboard
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("advanced-dashboard/", advanced_views.advanced_dashboard, name="advanced_dashboard"),
    
    # Authentication
    path("login/", auth_views.LoginView.as_view(template_name="core/login.html", redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="core:login"), name="logout"),
    path("register/", views.register_view, name="register"),

    # Appointments CRUD
    path("appointments/", views.pickup_list, name="pickup_list"),
    path("appointments/new/", views.pickup_create, name="pickup_create"),
    path("appointments/<int:pk>/", views.pickup_detail, name="pickup_detail"),
    path("appointments/<int:pk>/edit/", views.pickup_update, name="pickup_update"),
    path("appointments/<int:pk>/delete/", views.pickup_delete, name="pickup_delete"),
    path("appointments/<int:pk>/status/", views.pickup_status_update, name="pickup_status_update"),
    
    # Advanced Features
    path("smart-scheduling/", advanced_views.smart_scheduling, name="smart_scheduling"),
    path("appointment-calendar/", advanced_views.appointment_calendar, name="appointment_calendar"),
    path("appointment-search/", advanced_views.appointment_search, name="appointment_search"),
    path("pickup-map/", advanced_views.pickup_map, name="pickup_map"),

    # Service history
    path("history/", views.history_view, name="history"),

    # Notifications
    path("notifications/", views.notifications, name="notifications"),
    path("notifications/<int:pk>/read/", views.notification_mark_read, name="notification_mark_read"),
    
    # Profile and Settings
    path("profile/", views.profile_view, name="profile"),
    path("settings/", views.settings_view, name="settings"),
    path("tutorial/", views.tutorial_view, name="tutorial"),
    
    # API Endpoints
    path("api/notifications/<int:notification_id>/read/", api_views.mark_notification_read, name="api_mark_notification_read"),
    path("api/notifications/mark-all-read/", api_views.mark_all_notifications_read, name="api_mark_all_notifications_read"),
    path("api/appointments/stats/", api_views.get_appointment_stats, name="api_appointment_stats"),
    path("api/appointments/search/", api_views.search_appointments_api, name="api_search_appointments"),
    path("api/appointments/time-slots/", api_views.get_available_time_slots, name="api_time_slots"),
    path("api/appointments/<int:appointment_id>/", api_views.get_appointment_details, name="api_appointment_details"),
    path("api/appointments/<int:appointment_id>/update-status/", api_views.update_appointment_status, name="api_update_appointment_status"),
    path("api/route-optimization/", api_views.get_route_optimization, name="api_route_optimization"),
    path("api/map-appointments/", api_views.get_map_appointments, name="api_map_appointments"),
]


