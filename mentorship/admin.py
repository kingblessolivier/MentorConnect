from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import MentorAvailability, MentorshipRequest, Review


@admin.register(MentorAvailability)
class MentorAvailabilityAdmin(admin.ModelAdmin):
    """
    Admin for Mentor Availability Slots
    """
    list_display = (
        'mentor_display',
        'date_range_display',
        'time_display',
        'location_badge',
        'availability_status',
        'bookings_display',
    )
    list_filter = ('location_type', 'is_booked', 'date')
    search_fields = ('mentor__first_name', 'mentor__last_name', 'mentor__email', 'title')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-date', 'start_time')

    fieldsets = (
        (_('Mentor & Slot Details'), {
            'fields': ('mentor', 'title', 'description'),
            'classes': ('wide',)
        }),
        (_('Schedule'), {
            'fields': ('date', 'end_date', 'start_time', 'end_time'),
            'classes': ('wide',)
        }),
        (_('Location'), {
            'fields': ('location_type', 'location_address'),
            'classes': ('wide',)
        }),
        (_('Booking Settings'), {
            'fields': ('max_bookings', 'current_bookings'),
            'classes': ('wide',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('wide', 'collapse'),
        }),
    )

    def mentor_display(self, obj):
        return obj.mentor.get_full_name()
    mentor_display.short_description = _('Mentor')

    def date_range_display(self, obj):
        if obj.end_date and obj.end_date != obj.date:
            return format_html('{} → {}', obj.date, obj.end_date)
        return str(obj.date)
    date_range_display.short_description = _('Date(s)')
    date_range_display.admin_order_field = 'date'

    def time_display(self, obj):
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
    time_display.short_description = _('Time')

    def location_badge(self, obj):
        colors = {
            'in_person': '#DCFCE7',
            'virtual': '#FEF3C7',
            'hybrid': '#DBEAFE',
        }
        text_colors = {
            'in_person': '#15803D',
            'virtual': '#92400E',
            'hybrid': '#1E40AF',
        }
        color = colors.get(obj.location_type, '#E5E7EB')
        text_color = text_colors.get(obj.location_type, '#374151')
        label = obj.get_location_type_display()
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 11px;">{}</span>',
            color, text_color, label
        )
    location_badge.short_description = _('Location')

    def availability_status(self, obj):
        if obj.is_available:
            return format_html('<span style="color: #10B981; font-weight: bold;">✓ Available</span>')
        return format_html('<span style="color: #EF4444; font-weight: bold;">✗ Full</span>')
    availability_status.short_description = _('Status')

    def bookings_display(self, obj):
        return format_html(
            '<span style="background-color: #F3E8FF; color: #7C3AED; padding: 2px 8px; border-radius: 4px; font-weight: 600;">{}/{}</span>',
            obj.current_bookings, obj.max_bookings
        )
    bookings_display.short_description = _('Bookings')


@admin.register(MentorshipRequest)
class MentorshipRequestAdmin(admin.ModelAdmin):
    """
    Admin for Mentorship Requests
    """
    list_display = (
        'student_display',
        'mentor_display',
        'status_badge',
        'requested_duration_display',
        'created_at_short',
    )
    list_filter = ('status', 'created_at', 'mentor')
    search_fields = ('student__first_name', 'student__last_name', 'student__email', 'mentor__first_name', 'mentor__last_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        (_('Request Information'), {
            'fields': ('student', 'mentor', 'status'),
            'classes': ('wide',)
        }),
        (_('Details'), {
            'fields': ('message', 'requested_start_date', 'requested_end_date', 'meeting_link'),
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

    def mentor_display(self, obj):
        return obj.mentor.get_full_name()
    mentor_display.short_description = _('Mentor')

    def status_badge(self, obj):
        colors = {
            'pending': '#F59E0B',
            'approved': '#3B82F6',
            'scheduled': '#8B5CF6',
            'in_progress': '#10B981',
            'completed': '#06B6D4',
            'rejected': '#EF4444',
            'cancelled': '#9CA3AF',
        }
        color = colors.get(obj.status, '#9CA3AF')
        label = obj.get_status_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 11px;">{}</span>',
            color, label
        )
    status_badge.short_description = _('Status')

    def requested_duration_display(self, obj):
        if obj.requested_start_date and obj.requested_end_date:
            return f"{obj.requested_start_date} → {obj.requested_end_date}"
        return '—'
    requested_duration_display.short_description = _('Dates')

    def created_at_short(self, obj):
        return obj.created_at.strftime('%b %d, %Y')
    created_at_short.short_description = _('Requested')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin for Reviews/Ratings
    """
    list_display = (
        'student_display',
        'mentor_display',
        'rating_stars',
        'content_preview',
        'created_at_short',
    )
    list_filter = ('rating', 'created_at', 'mentor')
    search_fields = ('student__first_name', 'student__last_name', 'mentor__first_name', 'mentor__last_name', 'content', 'title')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        (_('Review Information'), {
            'fields': ('student', 'mentor', 'mentorship_request', 'rating', 'title'),
            'classes': ('wide',)
        }),
        (_('Review Content'), {
            'fields': ('content',),
            'classes': ('wide',)
        }),
        (_('Engagement'), {
            'fields': ('helpful_count',),
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

    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html(
            '<span style="color: #F59E0B; font-weight: bold; font-size: 12px;">{}</span> {}',
            stars, obj.rating
        )
    rating_stars.short_description = _('Rating')
    rating_stars.admin_order_field = 'rating'

    def content_preview(self, obj):
        preview = obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
        return preview
    content_preview.short_description = _('Review')

    def created_at_short(self, obj):
        return obj.created_at.strftime('%b %d, %Y')
    created_at_short.short_description = _('Reviewed')
    created_at_short.admin_order_field = 'created_at'
