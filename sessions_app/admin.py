from django.contrib import admin
from django.utils.html import format_html
from .models import Availability, Session


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    """
    Admin for Mentor Availability
    """
    list_display = (
        'mentor_display',
        'range_display',
        'session_type',
        'is_active_badge',
    )
    list_filter = ('session_type', 'is_active')
    search_fields = ('mentor__first_name', 'mentor__last_name', 'mentor__email')
    ordering = ('mentor', 'start')

    fieldsets = (
        ('Mentor', {
            'fields': ('mentor',),
            'classes': ('wide',)
        }),
        ('Availability Schedule', {
            'fields': ('start', 'end', 'session_type'),
            'classes': ('wide',)
        }),
        ('Status', {
            'fields': ('is_active',),
            'classes': ('wide',)
        }),
    )

    def mentor_display(self, obj):
        return obj.mentor.get_full_name()
    mentor_display.short_description = 'Mentor'
    mentor_display.admin_order_field = 'mentor__first_name'

    def day_display(self, obj):
        # legacy support; if using start/end show date
        if obj.start:
            return obj.start.strftime('%A')
        return ''
    day_display.short_description = 'Day'

    def range_display(self, obj):
        if obj.start and obj.end:
            return f"{obj.start.strftime('%b %d, %Y %H:%M')} - {obj.end.strftime('%b %d, %Y %H:%M')}"
        return ''
    range_display.short_description = 'Availability'

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #10B981; font-weight: bold;">✓ Active</span>')
        return format_html('<span style="color: #EF4444; font-weight: bold;">✗ Inactive</span>')
    is_active_badge.short_description = 'Status'


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
    list_filter = ('status', 'session_type', 'created_at')
    search_fields = ('student__first_name', 'student__last_name', 'mentor__first_name', 'mentor__last_name', 'mentor_notes', 'student_notes', 'title')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-start',)

    fieldsets = (
        ('Session Information', {
            'fields': ('student', 'mentor', 'availability', 'title', 'description'),
            'classes': ('wide',)
        }),
        ('Schedule', {
            'fields': ('start', 'end'),
            'classes': ('wide',)
        }),
        ('Meeting', {
            'fields': ('meeting_link',),
            'classes': ('wide',)
        }),
        ('Notes', {
            'fields': ('mentor_notes', 'student_notes'),
            'classes': ('wide',)
        }),
        ('Status', {
            'fields': ('status',),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('wide', 'collapse'),
        }),
    )

    def student_display(self, obj):
        return obj.student.get_full_name()
    student_display.short_description = 'Student'
    student_display.admin_order_field = 'student__first_name'

    def mentor_display(self, obj):
        return obj.mentor.get_full_name()
    mentor_display.short_description = 'Mentor'
    mentor_display.admin_order_field = 'mentor__first_name'

    def session_time(self, obj):
        if obj.start:
            start = obj.start.strftime('%b %d, %Y %H:%M')
        else:
            start = '—'
        if obj.end:
            end = obj.end.strftime('%b %d, %Y %H:%M')
            when = f"{start} — {end}"
        else:
            when = start
        return format_html('{}', when)
    session_time.short_description = 'When'
    session_time.admin_order_field = 'start'

    def status_badge(self, obj):
        colors = {
            'pending': '#F59E0B',
            'approved': '#3B82F6',
            'rejected': '#EF4444',
            'completed': '#10B981',
            'cancelled': '#9CA3AF',
        }
        color = colors.get(obj.status, '#9CA3AF')
        label = obj.get_status_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 11px;">{}</span>',
            color, label
        )
    status_badge.short_description = 'Status'

    def created_at_short(self, obj):
        return obj.created_at.strftime('%b %d, %Y')
    created_at_short.short_description = 'Booked'
    created_at_short.admin_order_field = 'created_at'
