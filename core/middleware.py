"""
Core Middleware
Custom middleware for language and theme handling
"""

from django.utils import translation
from django.conf import settings


class LanguageMiddleware:
    """
    Middleware to handle language switching and persistence
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # Get language from session, cookie, or default
            # Check custom site_language cookie first, then django_language
            language = request.session.get('django_language')

            if not language:
                language = request.COOKIES.get('site_language')

            if not language:
                language = request.COOKIES.get('django_language', settings.LANGUAGE_CODE)

            # Validate language is supported
            if language not in [lang[0] for lang in settings.LANGUAGES]:
                language = settings.LANGUAGE_CODE

            # Activate the language
            try:
                translation.activate(language)
            except Exception:
                # If translation activation fails, fall back to default
                translation.activate(settings.LANGUAGE_CODE)
                language = settings.LANGUAGE_CODE

            request.LANGUAGE_CODE = language

            response = self.get_response(request)

            # Set language cookies if not set
            if 'site_language' not in request.COOKIES:
                response.set_cookie('site_language', language, max_age=365*24*60*60)

            return response
        except Exception as e:
            # If anything fails, just pass through without translation
            request.LANGUAGE_CODE = settings.LANGUAGE_CODE
            return self.get_response(request)


class ThemeMiddleware:
    """
    Middleware to load active theme settings for each request
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Import here to avoid circular imports
        from core.models import ThemeSettings, SiteSettings

        try:
            # Get active theme and site settings
            request.theme = ThemeSettings.get_active_theme()
            request.site_settings = SiteSettings.get_settings()
        except Exception:
            # If database isn't ready yet, use None
            request.theme = None
            request.site_settings = None

        response = self.get_response(request)
        return response


class AccessibilityMiddleware:
    """
    Middleware to handle accessibility preferences
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get accessibility preferences from session/cookies
        request.high_contrast = request.session.get('high_contrast', False)
        request.large_text = request.session.get('large_text', False)
        request.text_to_speech = request.session.get('text_to_speech', False)

        response = self.get_response(request)
        return response
