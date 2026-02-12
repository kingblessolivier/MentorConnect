"""
Applications App
Guest student applications and invitation-based onboarding
"""

from django.apps import AppConfig


class ApplicationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'applications'
    verbose_name = 'Guest Applications'
