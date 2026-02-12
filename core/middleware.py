"""
Core Middleware
Custom middleware for language and theme handling
"""

from django.conf import settings


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
