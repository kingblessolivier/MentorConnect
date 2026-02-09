from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import StudentProfile, MentorProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """
    Admin for Student Profiles
    """
    list_display = (
        'user_name',
        'institution_display',
        'field_of_study_display',
        'completion_percentage',
        'profile_status',
        'updated_at_short',
    )
    list_filter = ('field_of_study', 'graduation_year', 'profile_completed', 'updated_at')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'institution', 'skills')
    readonly_fields = ('created_at', 'updated_at', 'completion_display')
    ordering = ('-updated_at',)

    fieldsets = (
        (_('User Information'), {
            'fields': ('user',),
            'classes': ('wide',)
        }),
        (_('Personal Information'), {
            'fields': ('bio', 'headline'),
            'classes': ('wide',)
        }),
        (_('Education'), {
            'fields': ('institution', 'field_of_study', 'graduation_year'),
            'classes': ('wide',)
        }),
        (_('Skills & Interests'), {
            'fields': ('skills', 'interests', 'goals'),
            'classes': ('wide',)
        }),
        (_('Documents'), {
            'fields': ('cv',),
            'classes': ('wide',)
        }),
        (_('Professional Links'), {
            'fields': ('linkedin_url', 'github_url', 'portfolio_url'),
            'classes': ('wide',)
        }),
        (_('Status'), {
            'fields': ('profile_completed', 'completion_display'),
            'classes': ('wide',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('wide', 'collapse'),
        }),
    )

    def user_name(self, obj):
        return obj.user.get_full_name()
    user_name.short_description = _('Student Name')
    user_name.admin_order_field = 'user__first_name'

    def institution_display(self, obj):
        return obj.institution or '—'
    institution_display.short_description = _('Institution')

    def field_of_study_display(self, obj):
        return obj.field_of_study or '—'
    field_of_study_display.short_description = _('Field')

    def completion_percentage(self, obj):
        percentage = obj.calculate_completion()
        color = '#10B981' if percentage >= 75 else '#F59E0B' if percentage >= 50 else '#EF4444'
        color_hex = color[1:]  # Remove # for CSS rgba
        return format_html(
            '<div style="background-color: #{hex}20; border-radius: 8px; padding: 4px 12px; font-weight: 600;"><span style="color: {color}">{percentage}</span>%</div>',
            hex=color_hex, color=color, percentage=percentage
        )
    completion_percentage.short_description = _('Completion')

    def profile_status(self, obj):
        if obj.profile_completed:
            return format_html('<span style="color: #10B981; font-weight: bold;">✓ Complete</span>')
        return format_html('<span style="color: #F59E0B; font-weight: bold;">⚠ Incomplete</span>')
    profile_status.short_description = _('Status')
    profile_status.admin_order_field = 'profile_completed'

    def completion_display(self, obj):
        return f"{obj.calculate_completion()}%"
    completion_display.short_description = _('Profile Completion')

    def updated_at_short(self, obj):
        return obj.updated_at.strftime('%b %d, %Y')
    updated_at_short.short_description = _('Updated')
    updated_at_short.admin_order_field = 'updated_at'


@admin.register(MentorProfile)
class MentorProfileAdmin(admin.ModelAdmin):
    """
    Admin for Mentor Profiles
    """
    list_display = (
        'user_name',
        'expertise_display',
        'experience_badge',
        'mentorship_types',
        'rating_display',
        'is_verified_badge',
    )
    list_filter = ('is_verified', 'accepts_in_person', 'accepts_virtual', 'updated_at')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'expertise', 'skills', 'company')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-updated_at',)

    fieldsets = (
        (_('User Information'), {
            'fields': ('user',),
            'classes': ('wide',)
        }),
        (_('Professional Information'), {
            'fields': ('headline', 'expertise', 'bio'),
            'classes': ('wide',)
        }),
        (_('Current Position'), {
            'fields': ('job_title', 'company'),
            'classes': ('wide',)
        }),
        (_('Experience'), {
            'fields': ('experience_years', 'skills'),
            'classes': ('wide',)
        }),
        (_('Location'), {
            'fields': ('city', 'country'),
            'classes': ('wide',)
        }),
        (_('Mentorship Details'), {
            'fields': (
                'session_duration',
                'hourly_rate',
                'accepts_in_person',
                'accepts_virtual',
                'min_internship_days',
                'max_internship_days',
            ),
            'classes': ('wide',)
        }),
        (_('Education'), {
            'fields': ('diploma', 'educational_institution'),
            'classes': ('wide',)
        }),
        (_('Professional Links'), {
            'fields': ('linkedin_url', 'twitter_url', 'github_url', 'website_url'),
            'classes': ('wide',)
        }),
        (_('Verification & Rating'), {
            'fields': ('is_verified', 'rating'),
            'classes': ('wide',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('wide', 'collapse'),
        }),
    )

    def user_name(self, obj):
        return obj.user.get_full_name()
    user_name.short_description = _('Mentor Name')
    user_name.admin_order_field = 'user__first_name'

    def expertise_display(self, obj):
        return obj.expertise or '—'
    expertise_display.short_description = _('Expertise')
    expertise_display.admin_order_field = 'expertise'

    def experience_badge(self, obj):
        years = obj.experience_years
        return format_html(
            '<span style="background-color: #DBEAFE; color: #1E40AF; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 11px;">{} years</span>',
            years
        )
    experience_badge.short_description = _('Experience')
    experience_badge.admin_order_field = 'experience_years'

    def mentorship_types(self, obj):
        types = []
        if obj.accepts_in_person:
            types.append(format_html('<span style="background-color: #DCFCE7; color: #15803D; padding: 2px 8px; border-radius: 4px; font-size: 10px; margin-right: 4px;">In-Person</span>'))
        if obj.accepts_virtual:
            types.append(format_html('<span style="background-color: #FEF3C7; color: #92400E; padding: 2px 8px; border-radius: 4px; font-size: 10px; margin-right: 4px;">Virtual</span>'))
        return format_html(' '.join(map(str, types)))
    mentorship_types.short_description = _('Types')

    def rating_display(self, obj):
        stars = '★' * int(obj.rating) + '☆' * (5 - int(obj.rating))
        return format_html(
            '<span style="color: #F59E0B; font-weight: bold; font-size: 12px;">{}</span> {}',
            stars, round(obj.rating, 1)
        )
    rating_display.short_description = _('Rating')
    rating_display.admin_order_field = 'rating'

    def is_verified_badge(self, obj):
        if obj.is_verified:
            return format_html('<span style="color: #10B981; font-weight: bold;">✓ Verified</span>')
        return format_html('<span style="color: #9CA3AF; font-weight: bold;">✗ Not Verified</span>')
    is_verified_badge.short_description = _('Verified')
    is_verified_badge.admin_order_field = 'is_verified'
