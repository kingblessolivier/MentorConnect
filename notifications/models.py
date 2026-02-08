"""
Notifications App Models
"""

from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    User notifications
    """
    TYPE_CHOICES = [
        ('follow', 'New Follower'),
        ('message', 'New Message'),
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('share', 'Share'),
        ('new_request', 'New Request'),
        ('request_approved', 'Request Approved'),
        ('request_rejected', 'Request Rejected'),
        ('session_booked', 'Session Booked'),
        ('session_cancelled', 'Session Cancelled'),
        ('session_reminder', 'Session Reminder'),
        ('system', 'System Notification'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications'
    )

    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    link = models.URLField(blank=True)

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} for {self.recipient.get_full_name()}"

    def mark_as_read(self):
        """Mark notification as read"""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def get_icon(self):
        """Get icon for notification type"""
        icons = {
            'follow': 'user-plus',
            'message': 'message-circle',
            'like': 'heart',
            'comment': 'message-square',
            'share': 'share-2',
            'new_request': 'file-text',
            'request_approved': 'check-circle',
            'request_rejected': 'x-circle',
            'session_booked': 'calendar',
            'session_cancelled': 'calendar-x',
            'session_reminder': 'bell',
            'system': 'info',
        }
        return icons.get(self.notification_type, 'bell')

    def get_absolute_url(self):
        """Get URL for notification - either link or notification list"""
        if self.link:
            return self.link
        return '/notifications/'

