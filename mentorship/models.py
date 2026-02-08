# Create your models here.
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class MentorAvailability(models.Model):
    """
    Mentor's availability calendar - observation internship slots
    For Mirror platform: 1-5 day shadowing opportunities
    """
    LOCATION_CHOICES = [
        ('in_person', _('In-Person (At Workplace)')),
        ('virtual', _('Virtual')),
        ('hybrid', _('Hybrid (Both)')),
    ]

    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='availability_slots'
    )

    # Date range for multi-day observation internships
    date = models.DateField(verbose_name=_('Start Date'))
    end_date = models.DateField(verbose_name=_('End Date'), null=True, blank=True)
    start_time = models.TimeField(verbose_name=_('Start Time'))
    end_time = models.TimeField(verbose_name=_('End Time'))

    # What the student will observe/learn
    title = models.CharField(max_length=200, verbose_name=_('What you will be doing'))
    description = models.TextField(blank=True, verbose_name=_('Additional details about the observation'))

    # Location type
    location_type = models.CharField(
        max_length=20,
        choices=LOCATION_CHOICES,
        default='in_person',
        verbose_name=_('Location Type')
    )
    location_address = models.TextField(
        blank=True,
        verbose_name=_('Location/Address'),
        help_text=_('Where the observation internship will take place')
    )

    # Booking settings
    is_booked = models.BooleanField(default=False)
    max_bookings = models.PositiveIntegerField(default=1, verbose_name=_('Max number of students'))
    current_bookings = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']
        verbose_name = _('Observation Slot')
        verbose_name_plural = _('Observation Slots')
        unique_together = ['mentor', 'date', 'start_time']

    def __str__(self):
        if self.end_date and self.end_date != self.date:
            return f"{self.mentor.get_full_name()} - {self.date} to {self.end_date}"
        return f"{self.mentor.get_full_name()} - {self.date} {self.start_time}-{self.end_time}"

    @property
    def is_available(self):
        return self.current_bookings < self.max_bookings

    @property
    def spots_left(self):
        return self.max_bookings - self.current_bookings

    @property
    def duration_days(self):
        """Return the number of days for this observation slot"""
        if self.end_date:
            return (self.end_date - self.date).days + 1
        return 1

    @property
    def is_in_person(self):
        return self.location_type in ['in_person', 'hybrid']


class MentorshipRequest(models.Model):
    """
    Request from a student to a mentor for observation internship (shadowing)
    Mirror Platform: 1-5 day observation internships
    """
    # Status stages for progress tracking
    STATUS_CHOICES = [
        ('pending', _('Pending Review')),
        ('approved', _('Approved - Awaiting Schedule')),
        ('scheduled', _('Scheduled')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('rejected', _('Rejected')),
        ('cancelled', _('Cancelled')),
    ]

    # Request type
    REQUEST_TYPE_CHOICES = [
        ('observation', _('Observation Internship (In-Person)')),
        ('virtual', _('Virtual Mentoring')),
        ('hybrid', _('Hybrid (Both)')),
    ]

    # Progress stages (1-5)
    STAGE_PENDING = 1
    STAGE_APPROVED = 2
    STAGE_SCHEDULED = 3
    STAGE_IN_PROGRESS = 4
    STAGE_COMPLETED = 5

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mentorship_requests_sent'
    )
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mentorship_requests_received'
    )

    # Request type
    request_type = models.CharField(
        max_length=20,
        choices=REQUEST_TYPE_CHOICES,
        default='observation',
        verbose_name=_('Type of Mentorship')
    )

    # Request details
    subject = models.CharField(max_length=200, verbose_name=_('Profession/Role of Interest'))
    message = models.TextField(verbose_name=_('Why do you want to shadow this professional?'))
    goals = models.TextField(blank=True, verbose_name=_('What do you hope to learn?'))

    # Observation internship duration
    requested_days = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Number of Days Requested'),
        help_text=_('How many days (1-5) would you like to shadow?')
    )

    # Student background (for mentor to review)
    current_education = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Current Education Level'),
        help_text=_('e.g., Final year secondary school, 2nd year Bachelor')
    )
    field_of_interest = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Field of Interest'),
        help_text=_('What field/profession are you considering?')
    )

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    mentor_response = models.TextField(blank=True, verbose_name=_('Mentor Response'))

    # NDA Agreement (required for observation internships)
    nda_agreed = models.BooleanField(
        default=False,
        verbose_name=_('NDA Agreement'),
        help_text=_('Student has agreed to Non-Disclosure Agreement')
    )
    nda_agreed_at = models.DateTimeField(null=True, blank=True)

    # Scheduling
    availability_slot = models.ForeignKey(
        MentorAvailability,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings'
    )
    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_time = models.TimeField(null=True, blank=True)
    meeting_link = models.URLField(blank=True, verbose_name=_('Meeting Link'))
    meeting_notes = models.TextField(blank=True, verbose_name=_('Meeting Notes'))

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Mentorship Request')
        verbose_name_plural = _('Mentorship Requests')

    def __str__(self):
        return f"{self.student.get_full_name()} -> {self.mentor.get_full_name()}: {self.subject}"

    @property
    def current_stage(self):
        """Return the current stage number (1-5)"""
        stage_map = {
            'pending': 1,
            'approved': 2,
            'scheduled': 3,
            'in_progress': 4,
            'completed': 5,
            'rejected': 0,
            'cancelled': 0,
        }
        return stage_map.get(self.status, 0)

    @property
    def progress_percentage(self):
        """Return progress as percentage (0-100)"""
        if self.status in ['rejected', 'cancelled']:
            return 0
        return (self.current_stage / 5) * 100

    @property
    def stage_info(self):
        """Return detailed stage information"""
        current = self.current_stage
        stages = [
            {'number': 1, 'name': 'Request Sent', 'status': 'completed' if current >= 1 else 'pending'},
            {'number': 2, 'name': 'Approved', 'status': 'completed' if current >= 2 else 'pending'},
            {'number': 3, 'name': 'Scheduled', 'status': 'completed' if current >= 3 else 'pending'},
            {'number': 4, 'name': 'In Progress', 'status': 'completed' if current >= 4 else 'pending'},
            {'number': 5, 'name': 'Completed', 'status': 'completed' if current >= 5 else 'pending'},
        ]
        # Mark current stage as 'current'
        if 1 <= current <= 5:
            stages[current - 1]['status'] = 'current'
        return stages

    def approve(self, response=''):
        """Approve the mentorship request"""
        from django.utils import timezone
        self.status = 'approved'
        self.mentor_response = response
        self.approved_at = timezone.now()
        self.save()

        # Create notification
        try:
            from notifications.models import Notification
            Notification.objects.create(
                recipient=self.student,
                sender=self.mentor,
                notification_type='request_approved',
                message=f'Your mentorship request "{self.subject}" has been approved! Please select a time slot.'
            )
        except Exception:
            pass

    def reject(self, response=''):
        """Reject the mentorship request"""
        self.status = 'rejected'
        self.mentor_response = response
        self.save()

        try:
            from notifications.models import Notification
            Notification.objects.create(
                recipient=self.student,
                sender=self.mentor,
                notification_type='request_rejected',
                message=f'Your mentorship request "{self.subject}" was not approved.'
            )
        except Exception:
            pass

    def schedule(self, availability_slot=None, scheduled_date=None, scheduled_time=None, meeting_link=''):
        """Schedule the mentorship session"""
        from django.utils import timezone
        self.status = 'scheduled'
        if availability_slot:
            self.availability_slot = availability_slot
            self.scheduled_date = availability_slot.date
            self.scheduled_time = availability_slot.start_time
            availability_slot.current_bookings += 1
            availability_slot.save()
        else:
            self.scheduled_date = scheduled_date
            self.scheduled_time = scheduled_time
        self.meeting_link = meeting_link
        self.scheduled_at = timezone.now()
        self.save()

        try:
            from notifications.models import Notification
            Notification.objects.create(
                recipient=self.student,
                sender=self.mentor,
                notification_type='session_scheduled',
                message=f'Your mentorship session "{self.subject}" has been scheduled for {self.scheduled_date}!'
            )
        except Exception:
            pass

    def start_session(self):
        """Mark the session as in progress"""
        from django.utils import timezone
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save()

    def complete(self, notes=''):
        """Mark mentorship as completed"""
        from django.utils import timezone
        self.status = 'completed'
        self.meeting_notes = notes
        self.completed_at = timezone.now()
        self.save()

        try:
            from notifications.models import Notification
            Notification.objects.create(
                recipient=self.student,
                sender=self.mentor,
                notification_type='session_completed',
                message=f'Your mentorship session "{self.subject}" has been completed! Please leave a review.'
            )
        except Exception:
            pass


class Review(models.Model):
    """
    Review/Rating from student to mentor
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given'
    )
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_received'
    )
    mentorship_request = models.ForeignKey(
        MentorshipRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews'
    )

    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_('Rating (1-5)')
    )
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField(verbose_name=_('Review'))

    # Helpful votes
    helpful_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['student', 'mentor', 'mentorship_request']
        verbose_name = _('Review')
        verbose_name_plural = _('Reviews')

    def __str__(self):
        return f"Review by {self.student.get_full_name()} for {self.mentor.get_full_name()}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update mentor's average rating
        try:
            self.mentor.mentor_profile.update_rating()
        except Exception:
            pass


class MentorshipGoal(models.Model):
    """
    Goals set within a mentorship relationship
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
    ]

    mentorship = models.ForeignKey(
        MentorshipRequest,
        on_delete=models.CASCADE,
        related_name='mentorship_goals'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(100)])

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
