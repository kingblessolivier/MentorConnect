from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import SiteSettings, ThemeSettings, ActivityLog, Translation, Testimonial, FAQ


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """
    Admin for Site Settings - Singleton model
    """
    list_display = ('site_name', 'maintenance_mode_badge', 'contact_email')

    fieldsets = (
        (_('Site Information'), {
            'fields': ('site_name', 'site_tagline', 'site_logo', 'site_favicon'),
            'classes': ('wide',)
        }),
        (_('Contact Information'), {
            'fields': ('contact_email', 'contact_phone', 'contact_address'),
            'classes': ('wide',)
        }),
        (_('Social Media'), {
            'fields': ('facebook_url', 'twitter_url', 'linkedin_url', 'instagram_url'),
            'classes': ('wide',)
        }),
        (_('Footer'), {
            'fields': ('footer_text',),
            'classes': ('wide',)
        }),
        (_('Feature Toggles'), {
            'fields': ('enable_chat', 'enable_feed', 'enable_notifications', 'enable_text_to_speech'),
            'classes': ('wide',)
        }),
        (_('Maintenance Mode'), {
            'fields': ('maintenance_mode', 'maintenance_message'),
            'classes': ('wide',)
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def maintenance_mode_badge(self, obj):
        if obj.maintenance_mode:
            return format_html('<span style="background-color: #FEE2E2; color: #DC2626; padding: 4px 12px; border-radius: 20px; font-weight: 600;">🔧 Maintenance</span>')
        return format_html('<span style="background-color: #D1FAE5; color: #059669; padding: 4px 12px; border-radius: 20px; font-weight: 600;">✓ Live</span>')
    maintenance_mode_badge.short_description = _('Status')


@admin.register(ThemeSettings)
class ThemeSettingsAdmin(admin.ModelAdmin):
    """
    Admin for Theme Settings
    """
    list_display = ('name', 'is_active_badge', 'primary_color_display', 'updated_at_short')
    list_filter = ('is_active', 'updated_at')
    ordering = ('-is_active', '-updated_at')

    fieldsets = (
        (_('Theme Information'), {
            'fields': ('name', 'is_active'),
            'classes': ('wide',)
        }),
        (_('Primary Colors'), {
            'fields': ('primary_color', 'primary_hover', 'primary_light'),
            'classes': ('wide',)
        }),
        (_('Secondary Colors'), {
            'fields': ('secondary_color', 'secondary_hover'),
            'classes': ('wide',)
        }),
        (_('Background & Text'), {
            'fields': ('background_color', 'surface_color', 'text_primary', 'text_secondary', 'text_muted'),
            'classes': ('wide',)
        }),
        (_('Status Colors'), {
            'fields': ('success_color', 'warning_color', 'error_color', 'info_color'),
            'classes': ('wide',)
        }),
        (_('Navbar & Footer'), {
            'fields': ('navbar_bg', 'navbar_text', 'footer_bg', 'footer_text'),
            'classes': ('wide',)
        }),
        (_('Styles'), {
            'fields': ('button_radius', 'card_radius'),
            'classes': ('wide',)
        }),
        (_('Shadows'), {
            'fields': ('shadow_sm', 'shadow_md', 'shadow_lg'),
            'classes': ('wide', 'collapse'),
        }),
    )

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #10B981; font-weight: bold;">✓ Active</span>')
        return format_html('<span style="color: #9CA3AF; font-weight: bold;">✗ Inactive</span>')
    is_active_badge.short_description = _('Active')

    def primary_color_display(self, obj):
        return format_html(
            '<div style="display: inline-block; width: 24px; height: 24px; background-color: {}; border-radius: 4px; border: 1px solid #e5e7eb;"></div> {}',
            obj.primary_color, obj.primary_color
        )
    primary_color_display.short_description = _('Primary Color')

    def updated_at_short(self, obj):
        return obj.updated_at.strftime('%b %d, %Y')
    updated_at_short.short_description = _('Updated')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """
    Admin for Activity Logs - Read-only monitoring
    """
    list_display = ('user_display', 'action_badge', 'ip_address', 'created_at_short')
    list_filter = ('action', 'created_at', 'user')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'ip_address', 'description')
    readonly_fields = ('user', 'action', 'description', 'ip_address', 'user_agent', 'extra_data', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def user_display(self, obj):
        if obj.user:
            return obj.user.get_full_name()
        return 'Anonymous'
    user_display.short_description = _('User')

    def action_badge(self, obj):
        colors = {
            'login': '#3B82F6',
            'logout': '#8B5CF6',
            'register': '#10B981',
            'profile_update': '#F59E0B',
            'mentor_request': '#EC4899',
            'session_book': '#06B6D4',
            'admin_action': '#EF4444',
        }
        color = colors.get(obj.action, '#9CA3AF')
        label = obj.get_action_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 11px;">{}</span>',
            color, label
        )
    action_badge.short_description = _('Action')

    def created_at_short(self, obj):
        return obj.created_at.strftime('%b %d, %Y %H:%M')
    created_at_short.short_description = _('Timestamp')


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    """
    Admin for Custom Translations
    """
    list_display = ('key', 'language_badge', 'text_preview', 'context')
    list_filter = ('language', 'updated_at')
    search_fields = ('key', 'text', 'context')
    ordering = ('key', 'language')

    fieldsets = (
        (_('Translation'), {
            'fields': ('key', 'language', 'text'),
            'classes': ('wide',)
        }),
        (_('Context'), {
            'fields': ('context',),
            'classes': ('wide',)
        }),
    )

    def language_badge(self, obj):
        flags = {'en': '🇬🇧', 'rw': '🇷🇼'}
        flag = flags.get(obj.language, '')
        return format_html('{} {}', flag, obj.get_language_display())
    language_badge.short_description = _('Language')

    def text_preview(self, obj):
        preview = obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
        return preview
    text_preview.short_description = _('Text')


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    """
    Admin for Testimonials
    """
    list_display = ('name_display', 'role', 'rating_stars', 'is_featured_badge', 'is_active_badge')
    list_filter = ('is_featured', 'is_active', 'rating', 'created_at')
    search_fields = ('name', 'role', 'company', 'content')
    ordering = ('-is_featured', '-created_at')

    fieldsets = (
        (_('Testimonial Information'), {
            'fields': ('name', 'role', 'company', 'photo'),
            'classes': ('wide',)
        }),
        (_('Content'), {
            'fields': ('content', 'rating'),
            'classes': ('wide',)
        }),
        (_('Status'), {
            'fields': ('is_featured', 'is_active'),
            'classes': ('wide',)
        }),
    )

    def name_display(self, obj):
        return f"{obj.name} ({obj.company or 'N/A'})"
    name_display.short_description = _('Name / Company')

    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: #F59E0B; font-weight: bold;">{}</span>', stars)
    rating_stars.short_description = _('Rating')

    def is_featured_badge(self, obj):
        if obj.is_featured:
            return format_html('<span style="color: #F59E0B; font-weight: bold;">⭐ Featured</span>')
        return '—'
    is_featured_badge.short_description = _('Featured')

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #10B981; font-weight: bold;">✓ Active</span>')
        return format_html('<span style="color: #EF4444; font-weight: bold;">✗ Inactive</span>')
    is_active_badge.short_description = _('Active')


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """
    Admin for FAQs
    """
    list_display = ('question', 'order_display', 'is_active_badge')
    list_filter = ('is_active', 'created_at')
    search_fields = ('question', 'answer')
    ordering = ('order', '-created_at')

    fieldsets = (
        (_('Question & Answer'), {
            'fields': ('question', 'answer'),
            'classes': ('wide',)
        }),
        (_('Settings'), {
            'fields': ('order', 'is_active'),
            'classes': ('wide',)
        }),
    )

    def order_display(self, obj):
        return f"#{obj.order}"
    order_display.short_description = _('Order')

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #10B981; font-weight: bold;">✓ Active</span>')
        return format_html('<span style="color: #EF4444; font-weight: bold;">✗ Inactive</span>')
    is_active_badge.short_description = _('Active')
