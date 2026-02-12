"""
Core Context Processors
Make theme, site settings, and language available to all templates
"""

from django.conf import settings


def theme_settings(request):
    """
    Add theme CSS variables to template context
    """
    from core.models import ThemeSettings

    try:
        theme = ThemeSettings.get_active_theme()
        css_vars = theme.to_css_variables() if theme else {}
    except Exception:
        css_vars = {}
        theme = None

    return {
        'theme': theme,
        'theme_css_vars': css_vars,
    }


def site_settings(request):
    """
    Add site settings to template context
    """
    from core.models import SiteSettings

    try:
        site = SiteSettings.get_settings()
    except Exception:
        site = None

    return {
        'site_settings': site,
        'SITE_NAME': site.site_name if site else settings.SITE_NAME,
        'SITE_TAGLINE': site.site_tagline if site else settings.SITE_TAGLINE,
    }


def language_settings(request):
    """
    Add language settings to template context
    Provides base translations (English) which will be translated by Google Translate widget
    """
    try:
        # Default to English as the base language for Google Translate
        current_language = 'en'

        # Translations dictionary for common UI elements
        # These are now just keys/English terms that Google Translate will translate in the browser
        t = {
            'home': 'Home',
            'about': 'About Us',
            'mentors': 'Mentors',
            'login': 'Login',
            'signup': 'Sign Up',
            'logout': 'Logout',
            'dashboard': 'Dashboard',
            'profile': 'Profile',
            'settings': 'Settings',
            'search': 'Search',
            'feed': 'Feed',
            'chat': 'Chat',
            'notifications': 'Notifications',
            'sessions': 'Sessions',
            'welcome': 'Welcome',
            'find_mentor': 'Find a Mentor',
            'become_mentor': 'Become a Mentor',
            'get_started': 'Get Started',
            'learn_more': 'Learn More',
            'contact_us': 'Contact Us',
            'follow': 'Follow',
            'unfollow': 'Unfollow',
            'book_session': 'Book Session',
            'send_message': 'Send Message',
            'view_profile': 'View Profile',
            'edit_profile': 'Edit Profile',
            'save': 'Save',
            'cancel': 'Cancel',
            'delete': 'Delete',
            'confirm': 'Confirm',
            'loading': 'Loading...',
            'no_results': 'No results found',
            'error': 'Error',
            'success': 'Success',
            'warning': 'Warning',
            'info': 'Information',
        }

        return {
            'current_language': current_language,
            'available_languages': settings.LANGUAGES,
            'translations': t,
            't': t,  # Shorthand
        }
    except Exception:
        return {
            'current_language': 'en',
            'available_languages': [('en', 'English')],
            'translations': {},
            't': {},
        }


def accessibility_settings(request):
    """
    Add accessibility preferences to template context
    """
    return {
        'high_contrast': getattr(request, 'high_contrast', False),
        'large_text': getattr(request, 'large_text', False),
        'text_to_speech_enabled': getattr(request, 'text_to_speech', False),
    }


def dashboard_context(request):
    """
    Add dashboard-related context for top navigation
    (messages, notifications counts and recent items)
    """
    context = {
        'unread_messages_count': 0,
        'unread_notifications_count': 0,
        'recent_conversations': [],
        'recent_notifications': [],
    }

    if not request.user.is_authenticated:
        return context

    try:
        from chat.models import Conversation, Message
        from notifications.models import Notification

        user = request.user

        # Get unread messages count
        context['unread_messages_count'] = Message.objects.filter(
            conversation__participants=user,
            is_read=False
        ).exclude(sender=user).count()

        # Get recent conversations (last 5)
        conversations = Conversation.objects.filter(
            participants=user
        ).prefetch_related('participants', 'messages').order_by('-updated_at')[:5]

        # Add other_participant to each conversation
        for conv in conversations:
            conv.other_participant = conv.get_other_participant(user)

        context['recent_conversations'] = conversations

        # Get unread notifications count
        context['unread_notifications_count'] = Notification.objects.filter(
            recipient=user,
            is_read=False
        ).count()

        # Get recent notifications (last 5)
        context['recent_notifications'] = Notification.objects.filter(
            recipient=user
        ).order_by('-created_at')[:5]

        # Mentor: pending counts for sidebar
        if user.is_mentor:
            try:
                from mentorship.models import MentorshipRequest
                context['pending_requests_count'] = MentorshipRequest.objects.filter(
                    mentor=user, status='pending'
                ).count()
            except Exception:
                context['pending_requests_count'] = 0
            try:
                from applications.models import GuestApplication
                context['guest_applications_pending_count'] = GuestApplication.objects.filter(
                    mentor=user, status='pending'
                ).count()
            except Exception:
                context['guest_applications_pending_count'] = 0
        else:
            context['guest_applications_pending_count'] = 0

    except Exception:
        pass

    return context

