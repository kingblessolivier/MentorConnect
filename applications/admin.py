"""
Applications Admin
"""

from django.contrib import admin
from .models import GuestApplication, InvitationToken


@admin.register(GuestApplication)
class GuestApplicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'mentor', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'school', 'interests']
    raw_id_fields = ['mentor', 'student']


@admin.register(InvitationToken)
class InvitationTokenAdmin(admin.ModelAdmin):
    list_display = ['application', 'token_preview', 'expires_at', 'used_at']
    list_filter = ['used_at']
    readonly_fields = ['token', 'created_at']

    def token_preview(self, obj):
        return f"{obj.token[:12]}..." if obj.token else "-"
    token_preview.short_description = 'Token'
