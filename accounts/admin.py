from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Custom admin for User model with enhanced features
    """
    list_display = (
        'email_display',
        'full_name',
        'role_badge',
        'status_badge',
        'date_joined_short',
    )
    list_filter = ('role', 'is_active', 'is_verified', 'email_verified', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)

    fieldsets = (
        (_('Authentication'), {
            'fields': ('email', 'password'),
            'classes': ('wide',)
        }),
        (_('Personal Information'), {
            'fields': ('first_name', 'last_name', 'phone', 'avatar'),
            'classes': ('wide',)
        }),
        (_('Role & Permissions'), {
            'fields': ('role', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('wide', 'collapse'),
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_verified', 'email_verified'),
            'classes': ('wide',)
        }),
        (_('Preferences'), {
            'fields': ('language',),
            'classes': ('wide',)
        }),
        (_('Important Dates'), {
            'fields': ('date_joined', 'last_login'),
            'classes': ('wide', 'collapse'),
        }),
    )

    readonly_fields = ('date_joined', 'last_login')
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'role'),
        }),
    )

    def email_display(self, obj):
        return f"✉️ {obj.email}"
    email_display.short_description = _('Email')

    def full_name(self, obj):
        return obj.get_full_name() or "N/A"
    full_name.short_description = _('Full Name')

    def role_badge(self, obj):
        colors = {
            'student': '#3B82F6',
            'mentor': '#8B5CF6',
            'admin': '#EF4444',
        }
        color = colors.get(obj.role, '#9CA3AF')
        label = obj.get_role_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 500; font-size: 11px;">{}</span>',
            color, label
        )
    role_badge.short_description = _('Role')

    def status_badge(self, obj):
        if obj.is_active:
            icon = '✓'
            color = '#10B981'
            status = 'Active'
        else:
            icon = '✗'
            color = '#EF4444'
            status = 'Inactive'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, status
        )
    status_badge.short_description = _('Status')

    def date_joined_short(self, obj):
        return obj.date_joined.strftime('%b %d, %Y')
    date_joined_short.short_description = _('Joined')
