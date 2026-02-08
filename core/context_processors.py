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
    """
    from django.utils import translation

    current_language = getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE)

    # Translations dictionary for common UI elements
    translations = {
        'en': {
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
        },
        'rw': {
            'home': 'Ahabanza',
            'about': 'Abo Turibo',
            'mentors': 'Abayobozi',
            'login': 'Kwinjira',
            'signup': 'Kwiyandikisha',
            'logout': 'Gusohoka',
            'dashboard': 'Ikibaho',
            'profile': 'Umwirondoro',
            'settings': 'Igenamiterere',
            'search': 'Gushakisha',
            'feed': 'Amakuru',
            'chat': 'Kuganira',
            'notifications': 'Amakuru mashya',
            'sessions': 'Ibyiciro',
            'welcome': 'Murakaza neza',
            'find_mentor': 'Shakisha Umuyobozi',
            'become_mentor': 'Ba Umuyobozi',
            'get_started': 'Tangira',
            'learn_more': 'Menya Byinshi',
            'contact_us': 'Twandikire',
            'follow': 'Kurikira',
            'unfollow': 'Kureka Gukurikira',
            'book_session': 'Gufata Igihe',
            'send_message': 'Ohereza Ubutumwa',
            'view_profile': 'Reba Umwirondoro',
            'edit_profile': 'Hindura Umwirondoro',
            'save': 'Bika',
            'cancel': 'Hagarika',
            'delete': 'Siba',
            'confirm': 'Emeza',
            'loading': 'Gutegereza...',
            'no_results': 'Nta bisubizo byabonetse',
            'error': 'Ikosa',
            'success': 'Byagenze neza',
            'warning': 'Umuburo',
            'info': 'Amakuru',
        }
    }

    return {
        'current_language': current_language,
        'available_languages': settings.LANGUAGES,
        'translations': translations.get(current_language, translations['en']),
        't': translations.get(current_language, translations['en']),  # Shorthand
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

    except Exception:
        pass

    return context

