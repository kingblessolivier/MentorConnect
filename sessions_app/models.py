"""
Sessions App Models
Availability, booking, and session management
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone


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
    # New datetime range support (optional alongside legacy day/time fields)
    start = models.DateTimeField(null=True, blank=True, help_text='Start datetime of availability')
    end = models.DateTimeField(null=True, blank=True, help_text='End datetime of availability')

    SESSION_TYPE_CHOICES = [
        ('online', _('online')),
        ('physical', _('physical')),
    ]

    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES, default='online')

    # Location fields
    location_name = models.CharField(max_length=200, blank=True, verbose_name='Location Name')
    address = models.TextField(blank=True, verbose_name='Address')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Latitude')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Longitude')

    is_active = models.BooleanField(default=True)
    is_booked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start']
        verbose_name = 'Availability'
        verbose_name_plural = 'Availabilities'

    def __str__(self):
        if self.start and self.end:
            return f"{self.mentor.get_full_name()} - {self.start.isoformat()} to {self.end.isoformat()}"
        # legacy fallback if old fields exist
        day = getattr(self, 'day_of_week', None)
        st = getattr(self, 'start_time', None)
        et = getattr(self, 'end_time', None)
        if day is not None and st and et:
            label = self.get_day_of_week_display() if hasattr(self, 'get_day_of_week_display') else str(day)
            return f"{self.mentor.get_full_name()} - {label} {st}-{et}"
        return f"{self.mentor.get_full_name()} - availability"

    def clean(self):
        # If start/end provided validate ordering
        if self.start and self.end and self.end <= self.start:
            raise ValidationError({'end': 'End must be after start.'})

    def overlaps(self, other_start, other_end):
        """Return True if this availability overlaps with given datetimes."""
        if not (self.start and self.end):
            return False
        return not (other_end <= self.start or other_start >= self.end)


class Session(models.Model):
    """
    Booked mentorship session
    """
    SESSION_TYPE_CHOICES = [
        ('online', _('online')),
        ('physical', _('physical')),
    ]

    STATUS_CHOICES = [
        ('pending', _('pending')),
        ('in_progress', _('in_progress')),
        ('approved', _('approved')),
        ('rejected', _('rejected')),
        ('completed', _('completed')),
        ('cancelled', _('cancelled')),
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
    # Link to availability slot that this booking is requested for
    availability = models.ForeignKey(
        Availability,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='booked_sessions'
    )

    # Session details
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)

    # Status of the booking lifecycle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

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
        ordering = ['-start']
        verbose_name = 'Session'
        verbose_name_plural = 'Sessions'

    def __str__(self):
        return f"{self.title or 'Session'} - {self.mentor.get_full_name()} & {self.student.get_full_name()}"

    def complete(self):
        """Mark session as completed"""
        self.status = 'completed'
        self.save()

    def approve(self, by_user=None):
        """Approve the session; mark availability as booked and set approved status."""
        if self.status != 'pending':
            return
        # prevent double booking: if availability already booked raise
        if self.availability and self.availability.is_booked:
            raise ValidationError('This availability is already booked')
        self.status = 'approved'
        self.save()
        if self.availability:
            self.availability.is_booked = True
            self.availability.save()

    def reject(self, reason=None):
        self.status = 'rejected'
        self.save()

    def cancel(self):
        """Cancel the session"""
        self.status = 'cancelled'
        self.save()
