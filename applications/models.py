"""
Applications App Models
Guest student applications, logged-in applications with payment workflow,
invitation tokens, and activity logging.
"""

import secrets
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import RegexValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def generate_invitation_token():
    """Generate secure random token for invitation link"""
    return secrets.token_urlsafe(32)


class GuestApplication(models.Model):
    """
    Guest student application - no account required to apply
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]

    # Applicant info (guest - no user account)
    name = models.CharField(_('Full Name'), max_length=200)
    email = models.EmailField(_('Email'))
    school = models.CharField(_('School/Institution'), max_length=200)
    interests = models.TextField(_('Interests'))
    message = models.TextField(_('Message'))
    cv = models.FileField(
        _('CV/Resume'),
        upload_to='applications/cvs/',
        blank=True,
        null=True
    )

    # Mentor (required)
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='guest_applications',
        limit_choices_to={'role': 'mentor'}
    )

    # Status and feedback
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    mentor_feedback = models.TextField(_('Mentor Feedback'), blank=True)

    # Link to user account after they register via invitation
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_guest_applications'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Guest Application')
        verbose_name_plural = _('Guest Applications')

    def __str__(self):
        return f"{self.name} -> {self.mentor.get_full_name()} ({self.get_status_display()})"

    def approve(self, feedback=''):
        """Approve the application and send invitation email"""
        self.status = 'approved'
        self.mentor_feedback = feedback
        self.approved_at = timezone.now()
        self.save()

    def reject(self, feedback=''):
        """Reject the application"""
        self.status = 'rejected'
        self.mentor_feedback = feedback
        self.rejected_at = timezone.now()
        self.save()


class InvitationToken(models.Model):
    """
    Secure token for invitation-based registration
    Links approved guest application to account creation
    """
    token = models.CharField(max_length=64, unique=True, db_index=True)
    application = models.OneToOneField(
        GuestApplication,
        on_delete=models.CASCADE,
        related_name='invitation_token'
    )
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Invitation Token')
        verbose_name_plural = _('Invitation Tokens')

    def __str__(self):
        return f"Invitation for {self.application.email}"

    @classmethod
    def create_for_application(cls, application):
        """Create invitation token for approved application"""
        token = cls.objects.create(
            token=generate_invitation_token(),
            application=application,
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )
        return token

    @property
    def is_valid(self):
        return (
            not self.used_at and
            self.expires_at > timezone.now()
        )


def generate_tracking_code():
    """Generate unique tracking code for applications (e.g. APP-XXXX)"""
    import random
    import string
    chars = string.ascii_uppercase + string.digits
    return 'APP-' + ''.join(random.choices(chars, k=8))


class Application(models.Model):
    """
    Logged-in student application for mentorship - requires payment to submit.
    Workflow: draft -> (pay) -> pending_finance -> finance verifies -> pending_review -> approved/rejected -> enrolled.
    """
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending_finance', _('Pending Finance')),
        ('finance_rejected', _('Finance Rejected')),
        ('pending_review', _('Pending Review')),
        ('review_rejected', _('Review Rejected')),
        ('approved', _('Approved')),
        ('enrolled', _('Enrolled')),
    ]

    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications'
    )
    mentorship_request = models.OneToOneField(
        'mentorship.MentorshipRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='application'
    )

    # Step 1: Personal Information
    name = models.CharField(_('Full Name'), max_length=200, blank=True)
    email = models.EmailField(_('Email'), blank=True, db_index=True)
    phone = models.CharField(_('Phone Number'), max_length=30, blank=True)
    date_of_birth = models.DateField(_('Date of Birth'), null=True, blank=True)
    age = models.PositiveIntegerField(_('Age'), null=True, blank=True, help_text=_('Calculated from DOB'))
    is_minor = models.BooleanField(_('Is Minor (under 18)'), default=False, db_index=True)
    parent_name = models.CharField(_('Parent/Guardian Name'), max_length=200, blank=True)
    parent_email = models.EmailField(_('Parent/Guardian Email'), blank=True)
    parent_phone = models.CharField(_('Parent/Guardian Phone'), max_length=30, blank=True)
    parent_contact = models.CharField(_('Parent/Guardian Contact'), max_length=200, blank=True)  # legacy/fallback
    parent_relationship = models.CharField(_('Relationship to Applicant'), max_length=50, blank=True)
    parent_consent_required = models.BooleanField(_('Parent Consent Required'), default=False)
    parent_consent_given = models.BooleanField(_('Parent Consent Given'), default=False)
    parent_notified = models.BooleanField(_('Parent Notified'), default=False)

    # Step 2: Academic & Goals
    school = models.CharField(_('School/University'), max_length=200, blank=True)
    program = models.CharField(_('Program of Study'), max_length=200, blank=True)
    department = models.CharField(_('Department/Field'), max_length=100, blank=True)
    career_goals = models.TextField(_('Career Goals'), blank=True)
    motivation = models.TextField(_('Motivation for Mentorship'), blank=True)
    expectations = models.TextField(_('Expectations from Mentor'), blank=True)

    # Step 3: Mentor Selection
    selected_mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications_received',
        limit_choices_to={'role': 'mentor'}
    )
    selected_availability_slot = models.ForeignKey(
        'mentorship.MentorAvailability',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications'
    )
    tracking_code = models.CharField(
        _('Tracking Code'),
        max_length=32,
        unique=True,
        db_index=True,
        default=generate_tracking_code
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True
    )
    locked = models.BooleanField(_('Locked'), default=False)
    message = models.TextField(_('Message'), blank=True)
    cv = models.FileField(
        _('CV/Resume'),
        upload_to='applications/cvs/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    current_step = models.PositiveIntegerField(_('Wizard Step'), default=1, help_text=_('1-5'))

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Application')
        verbose_name_plural = _('Applications')

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            self.tracking_code = generate_tracking_code()
        if self.date_of_birth and not self.age:
            from datetime import date
            today = date.today()
            self.age = today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        if self.date_of_birth:
            self.is_minor = self.age is not None and self.age < 18
        super().save(*args, **kwargs)

    @property
    def progress_percent(self):
        """Wizard progress 0-100"""
        return min(100, int((self.current_step / 5) * 100))

    def __str__(self):
        return f"{self.tracking_code} - {self.email or self.applicant_id} ({self.get_status_display()})"


class Payment(models.Model):
    """
    Payment record for an application. Student submits payment (e.g. receipt + transaction code);
    finance officer verifies before application moves to pending_review.
    """
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(_('Amount'), max_digits=10, decimal_places=2)
    transaction_code = models.CharField(
        _('Transaction Code'),
        max_length=64,
        unique=True,
        validators=[RegexValidator(r'^[A-Za-z0-9\-]+$', 'Only letters, numbers and hyphens allowed.')]
    )
    receipt = models.FileField(
        _('Receipt'),
        upload_to='payments/receipts/',
        blank=True,
        null=True
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(_('Verified'), default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_payments'
    )

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')

    def __str__(self):
        return f"{self.transaction_code} - {self.amount} ({'verified' if self.verified else 'pending'})"


class ActivityLog(models.Model):
    """
    Activity log for application workflow (status changes, payment verified, etc.)
    Table: applications_activitylog
    """
    ACTION_CHOICES = [
        ('status_change', _('Status Change')),
        ('payment_verified', _('Payment Verified')),
        ('payment_submitted', _('Payment Submitted')),
        ('note', _('Note')),
    ]

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES)
    previous_status = models.CharField(max_length=50, blank=True)
    new_status = models.CharField(max_length=50, blank=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='performed_activity_logs'
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = _('Application Activity Log')
        verbose_name_plural = _('Application Activity Logs')

    def __str__(self):
        return f"{self.action_type} at {self.timestamp}"


class ApplicationDraft(models.Model):
    """
    Draft application data (e.g. by session or user) before payment and submit.
    """
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    data = models.JSONField(default=dict, blank=True)
    is_guest = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='received_drafts'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='application_drafts'
    )

    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('Application Draft')
        verbose_name_plural = _('Application Drafts')

    def __str__(self):
        return f"Draft ({self.updated_at})"


class ApplicationWizardSession(models.Model):
    """
    Stores multi-step wizard progress for mentorship applications.
    For public applicants: session_key. For registered: user FK.
    """
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='wizard_sessions'
    )
    step_data = models.JSONField(default=dict, blank=True)  # {step: {field: value}}
    current_step = models.PositiveIntegerField(default=1)
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='wizard_session'
    )
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('Application Wizard Session')
        verbose_name_plural = _('Application Wizard Sessions')

    def __str__(self):
        return f"Wizard step {self.current_step} ({self.updated_at})"
