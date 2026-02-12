"""
Applications App Models
Guest student applications (no account required) and invitation tokens
"""

import secrets
from django.db import models
from django.conf import settings
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
