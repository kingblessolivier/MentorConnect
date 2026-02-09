from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin for Notifications
    """
    list_display = (
        'recipient_display',
        'notification_type_badge',
        'title_or_message',
        'read_status_badge',
        'created_at_short',
    )
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__first_name', 'recipient__last_name', 'recipient__email', 'title', 'message')
    readonly_fields = ('created_at', 'read_at')
    ordering = ('-created_at',)

    fieldsets = (
        (_('Notification Information'), {
            'fields': ('recipient', 'sender', 'notification_type', 'title', 'message'),
            'classes': ('wide',)
        }),
        (_('Link'), {
            'fields': ('link',),
            'classes': ('wide',)
        }),
        (_('Status'), {
            'fields': ('is_read', 'read_at'),
            'classes': ('wide',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('wide', 'collapse'),
        }),
    )

    def recipient_display(self, obj):
        return obj.recipient.get_full_name()
    recipient_display.short_description = _('To')
    recipient_display.admin_order_field = 'recipient__first_name'

    def notification_type_badge(self, obj):
        colors = {
            'follow': '#3B82F6',
            'message': '#8B5CF6',
            'like': '#EC4899',
            'comment': '#F59E0B',
            'share': '#10B981',
            'new_request': '#06B6D4',
            'request_approved': '#10B981',
            'request_rejected': '#EF4444',
            'session_booked': '#3B82F6',
            'session_cancelled': '#EF4444',
            'session_reminder': '#F59E0B',
            'system': '#9CA3AF',
        }
        color = colors.get(obj.notification_type, '#9CA3AF')
        label = obj.get_notification_type_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-weight: 600; font-size: 11px;">{}</span>',
            color, label
        )
    notification_type_badge.short_description = _('Type')

    def title_or_message(self, obj):
        text = obj.title or obj.message
        preview = text[:60] + '...' if len(text) > 60 else text
        return preview
    title_or_message.short_description = _('Content')

    def read_status_badge(self, obj):
        if obj.is_read:
            return format_html('<span style="color: #10B981; font-weight: bold;">✓ Read</span>')
        return format_html('<span style="color: #F59E0B; font-weight: bold;">○ Unread</span>')
    read_status_badge.short_description = _('Status')

    def created_at_short(self, obj):
        return obj.created_at.strftime('%b %d, %Y %H:%M')
    created_at_short.short_description = _('Sent')
    created_at_short.admin_order_field = 'created_at'
