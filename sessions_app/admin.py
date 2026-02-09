from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Availability, Session


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    """
    Admin for Mentor Availability
    """
    list_display = (
        'mentor_display',
        'day_display',
        'time_display',
        'is_active_badge',
    )
    list_filter = ('day_of_week', 'is_active')
    search_fields = ('mentor__first_name', 'mentor__last_name', 'mentor__email')
    ordering = ('mentor', 'day_of_week', 'start_time')

    fieldsets = (
        (_('Mentor'), {
            'fields': ('mentor',),
            'classes': ('wide',)
        }),
        (_('Availability Schedule'), {
            'fields': ('day_of_week', 'start_time', 'end_time'),
            'classes': ('wide',)
        }),
        (_('Status'), {
            'fields': ('is_active',),
            'classes': ('wide',)
        }),
    )

    def mentor_display(self, obj):
        return obj.mentor.get_full_name()
    mentor_display.short_description = _('Mentor')
    mentor_display.admin_order_field = 'mentor__first_name'

    def day_display(self, obj):
        return obj.get_day_of_week_display()
    day_display.short_description = _('Day')

    def time_display(self, obj):
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
    time_display.short_description = _('Hours')

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #10B981; font-weight: bold;">✓ Active</span>')
        return format_html('<span style="color: #EF4444; font-weight: bold;">✗ Inactive</span>')
    is_active_badge.short_description = _('Status')


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """
    Admin for Booked Sessions
    """
    list_display = (
        'student_display',
        'mentor_display',
        'session_time',
        'status_badge',
        'created_at_short',
    )
    list_filter = ('status', 'scheduled_time', 'created_at')
    search_fields = ('student__first_name', 'student__last_name', 'mentor__first_name', 'mentor__last_name', 'mentor_notes', 'student_notes', 'title')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-scheduled_time',)

    fieldsets = (
        (_('Session Information'), {
            'fields': ('student', 'mentor', 'mentorship_request', 'title', 'description'),
            'classes': ('wide',)
        }),
        (_('Schedule'), {
            'fields': ('scheduled_time', 'duration'),
            'classes': ('wide',)
        }),
        (_('Meeting'), {
            'fields': ('meeting_link',),
            'classes': ('wide',)
        }),
        (_('Notes'), {
            'fields': ('mentor_notes', 'student_notes'),
            'classes': ('wide',)
        }),
        (_('Status'), {
            'fields': ('status',),
            'classes': ('wide',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('wide', 'collapse'),
        }),
    )

    def student_display(self, obj):
        return obj.student.get_full_name()
    student_display.short_description = _('Student')
    student_display.admin_order_field = 'student__first_name'

    def mentor_display(self, obj):
        return obj.mentor.get_full_name()
    mentor_display.short_description = _('Mentor')
    mentor_display.admin_order_field = 'mentor__first_name'

    def session_time(self, obj):
        scheduled = obj.scheduled_time.strftime('%b %d, %Y %H:%M')
        duration = f"{obj.duration} min" if obj.duration else '—'
        return format_html('{} <br/> <small style="color: #9CA3AF;">{}</small>', scheduled, duration)
    session_time.short_description = _('When')
    session_time.admin_order_field = 'scheduled_time'

    def status_badge(self, obj):
        colors = {
            'scheduled': '#3B82F6',
            'in_progress': '#F59E0B',
            'completed': '#10B981',
            'cancelled': '#EF4444',
            'no_show': '#EC4899',
        }
        color = colors.get(obj.status, '#9CA3AF')
        label = obj.get_status_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 11px;">{}</span>',
            color, label
        )
    status_badge.short_description = _('Status')

    def created_at_short(self, obj):
        return obj.created_at.strftime('%b %d, %Y')
    created_at_short.short_description = _('Booked')
    created_at_short.admin_order_field = 'created_at'
