"""
Applications Services
Email sending and token handling
"""

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone


def send_approval_email(application):
    """Send invitation email when mentor approves guest application"""
    from .models import InvitationToken

    # Delete old tokens for this application, create new one
    InvitationToken.objects.filter(application=application).delete()
    token_obj = InvitationToken.create_for_application(application)

    # Build absolute URL for registration
    domain = getattr(settings, 'SITE_DOMAIN', None) or (
        settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost'
    )
    if settings.DEBUG and domain == 'localhost':
        domain = 'localhost:8000'
    scheme = 'https' if not settings.DEBUG else 'http'
    path = reverse('applications:register_with_token', kwargs={'token': token_obj.token})
    registration_url = f"{scheme}://{domain}{path}"

    subject = f"Your application has been approved - {getattr(settings, 'SITE_NAME', 'MentorConnect')}"
    message = f"""Hello {application.name},

Great news! Your application to mentor {application.mentor.get_full_name()} has been approved.

{f'Mentor feedback: {application.mentor_feedback}' if application.mentor_feedback else ''}

To continue and create your account, please click the link below. This link will expire in 7 days.

{registration_url}

After registering, you'll be able to:
- View mentor feedback
- Schedule sessions
- Continue your mentorship journey

Best regards,
{getattr(settings, 'SITE_NAME', 'MentorConnect')} Team
"""
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@mentorconnect.local'),
        recipient_list=[application.email],
        fail_silently=True,
    )
