"""
Notifications App Views
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    """List all notifications"""
    template_name = 'notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


@login_required
def mark_as_read(request, pk):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.mark_as_read()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    if notification.link:
        return redirect(notification.link)
    return redirect('notifications:list')


@login_required
def mark_all_as_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(
        recipient=request.user, is_read=False
    ).update(is_read=True)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    return redirect('notifications:list')


@login_required
def unread_count(request):
    """Get unread notification count"""
    count = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()
    return JsonResponse({'count': count})


@login_required
def recent_notifications(request):
    """Get recent notifications for dropdown"""
    notifications = Notification.objects.filter(
        recipient=request.user
    )[:5]

    data = [{
        'id': n.id,
        'type': n.notification_type,
        'message': n.message,
        'is_read': n.is_read,
        'icon': n.get_icon(),
        'created_at': n.created_at.strftime('%b %d, %H:%M'),
    } for n in notifications]

    return JsonResponse({'notifications': data})
