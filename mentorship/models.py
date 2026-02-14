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


class MentorFacilitator(models.Model):
    """
    Staff role: mentor facilitator - assigned by admin. Handles disputes and session reports.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mentor_facilitator_profile'
    )
    bio = models.TextField(blank=True)
    assigned_since = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Mentor Facilitator')
        verbose_name_plural = _('Mentor Facilitators')

    def __str__(self):
        return str(self.user.get_full_name())


class MentorFacilitatorAssignment(models.Model):
    """Assignment of a facilitator to a mentor or a specific mentorship request."""
    facilitator = models.ForeignKey(
        MentorFacilitator,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='facilitator_assignments'
    )
    mentorship_request = models.ForeignKey(
        MentorshipRequest,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='facilitator_assignments'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('facilitator', 'mentor', 'mentorship_request')]
        verbose_name = _('Mentor Facilitator Assignment')
        verbose_name_plural = _('Mentor Facilitator Assignments')

    def __str__(self):
        return f"{self.facilitator} -> {self.mentor or self.mentorship_request}"


class Dispute(models.Model):
    """Dispute raised on a mentorship request - handled by facilitator or admin."""
    STATUS_CHOICES = [
        ('open', _('Open')),
        ('under_review', _('Under Review')),
        ('resolved', _('Resolved')),
        ('escalated', _('Escalated')),
    ]

    mentorship_request = models.ForeignKey(
        MentorshipRequest,
        on_delete=models.CASCADE,
        related_name='disputes'
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='disputes_reported'
    )
    facilitator = models.ForeignKey(
        MentorFacilitator,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='disputes_handled'
    )
    description = models.TextField(_('Description'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    admin_override = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Dispute')
        verbose_name_plural = _('Disputes')

    def __str__(self):
        return f"Dispute #{self.id} - {self.mentorship_request} ({self.get_status_display()})"


class SessionReport(models.Model):
    """Session report (e.g. from mentor or facilitator) for a mentorship session."""
    ATTENDANCE_CHOICES = [
        ('attended', _('Attended')),
        ('missed', _('Missed')),
        ('partial', _('Partial')),
    ]

    mentorship_request = models.ForeignKey(
        MentorshipRequest,
        on_delete=models.CASCADE,
        related_name='session_reports'
    )
    session_date = models.DateField(_('Session Date'))
    session_time = models.TimeField(_('Session Time'))
    duration_minutes = models.PositiveIntegerField(_('Duration (minutes)'))
    summary_notes = models.TextField(_('Summary'), blank=True)
    attendance_status = models.CharField(
        max_length=20,
        choices=ATTENDANCE_CHOICES,
        default='attended'
    )
    mentor_feedback = models.TextField(blank=True)
    student_feedback = models.TextField(blank=True)
    approved_by_facilitator = models.BooleanField(default=False)
    flagged_issue = models.BooleanField(default=False)
    escalated_to_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-session_date', '-session_time']
        verbose_name = _('Session Report')
        verbose_name_plural = _('Session Reports')

    def __str__(self):
        return f"Report {self.session_date} - {self.mentorship_request}"


class MentorshipAnalytics(models.Model):
    """
    Advanced analytics and tracking for mentorship relationships.
    Tracks KPIs, success metrics, and performance indicators.
    """
    mentorship = models.OneToOneField(
        MentorshipRequest,
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    
    # Success metrics
    success_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        help_text=_('Overall success score (0-10) based on multiple factors')
    )
    engagement_level = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_('Engagement level percentage based on session attendance and interactions')
    )
    goal_completion_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_('Percentage of mentorship goals completed')
    )
    session_attendance_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_('Percentage of sessions attended')
    )
    
    # Time metrics
    time_to_match = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Time in hours from request to approval')
    )
    time_to_schedule = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Time in hours from approval to scheduling')
    )
    time_to_completion = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Time in hours from start to completion')
    )
    total_duration_hours = models.PositiveIntegerField(
        default=0,
        help_text=_('Total mentorship duration in hours')
    )
    
    # Quality metrics
    student_satisfaction = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text=_('Student satisfaction score (0-5)')
    )
    mentor_satisfaction = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text=_('Mentor satisfaction score (0-5)')
    )
    skill_improvement_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        help_text=_('Measured skill improvement (0-10)')
    )
    
    # Risk indicators
    at_risk_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        help_text=_('Risk score indicating potential issues (0-10)')
    )
    intervention_needed = models.BooleanField(default=False)
    last_intervention_at = models.DateTimeField(null=True, blank=True)
    
    # Analytics metadata
    calculated_at = models.DateTimeField(auto_now=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Mentorship Analytics')
        verbose_name_plural = _('Mentorship Analytics')
        ordering = ['-calculated_at']
    
    def __str__(self):
        return f"Analytics for {self.mentorship}"
    
    def calculate_success_score(self):
        """Calculate overall success score based on multiple factors"""
        from django.utils import timezone
        
        factors = []
        weights = []
        
        # Goal completion (weight: 30%)
        factors.append(self.goal_completion_rate / 10.0)  # Convert 0-100 to 0-10
        weights.append(0.3)
        
        # Session attendance (weight: 20%)
        factors.append(self.session_attendance_rate / 10.0)
        weights.append(0.2)
        
        # Student satisfaction (weight: 25%)
        factors.append(self.student_satisfaction * 2)  # Convert 0-5 to 0-10
        weights.append(0.25)
        
        # Mentor satisfaction (weight: 15%)
        factors.append(self.mentor_satisfaction * 2)  # Convert 0-5 to 0-10
        weights.append(0.15)
        
        # Skill improvement (weight: 10%)
        factors.append(self.skill_improvement_score)
        weights.append(0.1)
        
        # Calculate weighted average
        weighted_sum = sum(f * w for f, w in zip(factors, weights))
        total_weight = sum(weights)
        
        self.success_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        self.calculated_at = timezone.now()
        self.save()
    
    def update_engagement_level(self):
        """Update engagement level based on recent activity"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Calculate based on session reports, messages, and interactions
        # This is a simplified version - would be expanded in real implementation
        total_sessions = self.mentorship.session_reports.count()
        attended_sessions = self.mentorship.session_reports.filter(
            attendance_status='attended'
        ).count()
        
        if total_sessions > 0:
            session_engagement = (attended_sessions / total_sessions) * 100
        else:
            session_engagement = 0
        
        # Consider other engagement factors (simplified)
        self.engagement_level = min(100.0, session_engagement * 0.7 + 30.0)  # Base + session weight
        self.save()
    
    def calculate_risk_score(self):
        """Calculate risk score for early intervention"""
        risk_factors = []
        
        # Low engagement
        if self.engagement_level < 50:
            risk_factors.append(7.0)
        elif self.engagement_level < 70:
            risk_factors.append(4.0)
        
        # Missed sessions
        total_sessions = self.mentorship.session_reports.count()
        missed_sessions = self.mentorship.session_reports.filter(
            attendance_status='missed'
        ).count()
        
        if total_sessions > 0 and missed_sessions / total_sessions > 0.3:
            risk_factors.append(8.0)
        
        # Low satisfaction
        if self.student_satisfaction < 2.5 or self.mentor_satisfaction < 2.5:
            risk_factors.append(6.0)
        
        # Calculate average risk
        if risk_factors:
            self.at_risk_score = sum(risk_factors) / len(risk_factors)
            self.intervention_needed = self.at_risk_score > 5.0
        else:
            self.at_risk_score = 0.0
            self.intervention_needed = False
        
        self.save()
