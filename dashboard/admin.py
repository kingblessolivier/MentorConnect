from django.contrib import admin
from django.utils.html import format_html
from .models import ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'status_badge', 'is_read', 'replied_at')
    list_filter = ('status', 'is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message', 'admin_notes')
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at', 'replied_at')
    actions = ['mark_as_read', 'mark_as_replied', 'mark_as_closed']
    
    fieldsets = (
        ('Message Details', {
            'fields': ('name', 'email', 'subject', 'message', 'created_at')
        }),
        ('Admin Management', {
            'fields': ('status', 'is_read', 'admin_notes', 'replied_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        color_map = {
            'new': 'blue',
            'read': 'gray', 
            'replied': 'green',
            'closed': 'red'
        }
        color = color_map.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True, status='read')
        self.message_user(request, f'{updated} message(s) marked as read.')
    mark_as_read.short_description = 'Mark selected messages as read'
    
    def mark_as_replied(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='replied', replied_at=timezone.now())
        self.message_user(request, f'{updated} message(s) marked as replied.')
    mark_as_replied.short_description = 'Mark selected messages as replied'
    
    def mark_as_closed(self, request, queryset):
        updated = queryset.update(status='closed')
        self.message_user(request, f'{updated} message(s) marked as closed.')
    mark_as_closed.short_description = 'Mark selected messages as closed'
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-created_at')
