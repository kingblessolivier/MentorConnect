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
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
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
        verbose_name = _('Availability')
        verbose_name_plural = _('Availabilities')

    def __str__(self):
        return f"{self.mentor.get_full_name()} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class Session(models.Model):
    """
    Booked mentorship session
    """
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
    duration = models.PositiveIntegerField(default=60, help_text=_('Duration in minutes'))

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    # Meeting link (for virtual sessions)
    meeting_link = models.URLField(blank=True)

    # Notes
    mentor_notes = models.TextField(blank=True)
    student_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_time']
        verbose_name = _('Session')
        verbose_name_plural = _('Sessions')

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
