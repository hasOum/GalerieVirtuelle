from .models import Notification, Panier


def notifications_context(request):
    """Add unread notifications count to context"""
    context = {}
    
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            utilisateur=request.user,
            statut=Notification.Statut.NON_LUE
        ).count()
        context['unread_notifications_count'] = unread_count
    else:
        context['unread_notifications_count'] = 0
    
    return context


def cart_count(request):
    """Add cart count to context"""
    context = {'cart_count': 0}
    
    if request.user.is_authenticated:
        panier = Panier.objects.filter(client=request.user).first()
        if panier:
            context['cart_count'] = panier.items.count()
    
    return context
