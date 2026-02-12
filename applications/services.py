"""
Applications Services
Email sending and token handling
"""

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags


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

    site_name = getattr(settings, 'SITE_NAME', 'MentorConnect')
    subject = f"Your application has been approved - {site_name}"

    context = {
        'application': application,
        'registration_url': registration_url,
        'site_name': site_name,
    }

    html_message = render_to_string('emails/approval_email.html', context)
    message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@mentorconnect.local'),
        recipient_list=[application.email],
        fail_silently=True,
        html_message=html_message,
    )
