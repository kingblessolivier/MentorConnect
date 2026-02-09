from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """
    Admin for Conversations
    """
    list_display = (
        'participants_display',
        'last_message_preview',
        'message_count_display',
        'updated_at_short',
    )
    list_filter = ('created_at', 'updated_at')
    search_fields = ('participants__first_name', 'participants__last_name', 'participants__email')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-updated_at',)

    fieldsets = (
        (_('Conversation'), {
            'fields': ('participants',),
            'classes': ('wide',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('wide', 'collapse'),
        }),
    )

    def participants_display(self, obj):
        names = [p.get_full_name() for p in obj.participants.all()]
        return ' ↔️ '.join(names)
    participants_display.short_description = _('Participants')

    def last_message_preview(self, obj):
        last_msg = obj.get_last_message()
        if last_msg:
            preview = last_msg.content[:50] + '...' if len(last_msg.content) > 50 else last_msg.content
            sender = last_msg.sender.get_full_name()
            return format_html('<strong>{}:</strong> {}', sender, preview)
        return format_html('<em style="color: #9CA3AF;">No messages</em>')
    last_message_preview.short_description = _('Last Message')

    def message_count_display(self, obj):
        count = obj.messages.count()
        return format_html('<span style="background-color: #DBEAFE; color: #1E40AF; padding: 2px 8px; border-radius: 4px; font-weight: 600;">{} messages</span>', count)
    message_count_display.short_description = _('Messages')

    def updated_at_short(self, obj):
        return obj.updated_at.strftime('%b %d, %Y %H:%M')
    updated_at_short.short_description = _('Last Activity')
    updated_at_short.admin_order_field = 'updated_at'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Admin for Messages
    """
    list_display = (
        'sender_display',
        'conversation_link',
        'message_preview',
        'read_status_badge',
        'created_at_short',
    )
    list_filter = ('is_read', 'created_at', 'conversation')
    search_fields = ('sender__first_name', 'sender__last_name', 'sender__email', 'content')
    readonly_fields = ('created_at', 'read_at')
    ordering = ('-created_at',)

    fieldsets = (
        (_('Message Information'), {
            'fields': ('conversation', 'sender', 'content', 'attachment'),
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

    def sender_display(self, obj):
        return obj.sender.get_full_name()
    sender_display.short_description = _('From')
    sender_display.admin_order_field = 'sender__first_name'

    def conversation_link(self, obj):
        participants = [p.get_full_name() for p in obj.conversation.participants.all()]
        return ' ↔️ '.join(participants)
    conversation_link.short_description = _('Conversation')

    def message_preview(self, obj):
        preview = obj.content[:60] + '...' if len(obj.content) > 60 else obj.content
        return preview
    message_preview.short_description = _('Message')

    def read_status_badge(self, obj):
        if obj.is_read:
            return format_html('<span style="color: #10B981; font-weight: bold;">✓ Read</span>')
        return format_html('<span style="color: #F59E0B; font-weight: bold;">○ Unread</span>')
    read_status_badge.short_description = _('Status')

    def created_at_short(self, obj):
        return obj.created_at.strftime('%b %d, %Y %H:%M')
    created_at_short.short_description = _('Sent')
    created_at_short.admin_order_field = 'created_at'
