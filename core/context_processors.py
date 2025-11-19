from .models import Notification

def navbar_context(request):
    """
    Context processor to add navbar-related data to all templates
    """
    context = {}
    
    if request.user.is_authenticated:
        context['unread_notifications'] = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
    else:
        context['unread_notifications'] = 0
    
    return context
