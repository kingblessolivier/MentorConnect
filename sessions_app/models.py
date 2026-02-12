"""
Sessions App Models
Availability, booking, and session management
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Availability(models.Model):
    """
    Mentor availability slots
    """
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='availabilities'
    )
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['day_of_week', 'start_time']
        verbose_name = 'Availability'
        verbose_name_plural = 'Availabilities'

    def __str__(self):
        return f"{self.mentor.get_full_name()} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class Session(models.Model):
    """
    Booked mentorship session
    """
    SESSION_TYPE_CHOICES = [
        ('online', _('Online')),
        ('physical', _('Physical / In-Person')),
    ]

    STATUS_CHOICES = [
        ('scheduled', _('Scheduled')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('no_show', _('No Show')),
    ]

    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mentor_sessions'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_sessions'
    )
    mentorship_request = models.ForeignKey(
        'mentorship.MentorshipRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessions'
    )

    # Session details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    scheduled_time = models.DateTimeField()
    duration = models.PositiveIntegerField(default=60, help_text='Duration in minutes')

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    # Session type and location (for physical sessions)
    session_type = models.CharField(
        max_length=20,
        choices=SESSION_TYPE_CHOICES,
        default='online',
        verbose_name='Session Type'
    )
    location_name = models.CharField(max_length=200, blank=True, verbose_name='Location Name')
    address = models.TextField(blank=True, verbose_name='Address')
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        verbose_name='Latitude'
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        verbose_name='Longitude'
    )

    # Meeting link (for online sessions)
    meeting_link = models.URLField(blank=True)

    # Attendance tracking
    student_attended = models.BooleanField(null=True, blank=True, verbose_name='Student Attended')
    mentor_attended = models.BooleanField(null=True, blank=True, verbose_name='Mentor Attended')

    # Notes
    mentor_notes = models.TextField(blank=True)
    student_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_time']
        verbose_name = 'Session'
        verbose_name_plural = 'Sessions'

    def __str__(self):
        return f"{self.title} - {self.mentor.get_full_name()} & {self.student.get_full_name()}"

    def complete(self):
        """Mark session as completed"""
        self.status = 'completed'
        self.save()

    def cancel(self):
        """Cancel the session"""
        self.status = 'cancelled'
        self.save()
