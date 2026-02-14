"""
Core App Models
Site settings, theme configuration, and system-wide models
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class SiteSettings(models.Model):
    """
    Singleton model for site-wide settings
    Admin can change site name, logo, and other configurations
    """
    site_name = models.CharField(max_length=100, default='MentorConnect')
    site_tagline = models.CharField(max_length=255, default='Connect with mentors, grow your future')
    site_logo = models.ImageField(upload_to='site/', blank=True, null=True)
    site_favicon = models.ImageField(upload_to='site/', blank=True, null=True)

    # Contact Information
    contact_email = models.EmailField(default='contact@mentorconnect.com')
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_address = models.TextField(blank=True)

    # Social Media Links
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)

    # Footer Text
    footer_text = models.TextField(default='© 2026 MentorConnect. All rights reserved.')

    # Feature Toggles
    enable_chat = models.BooleanField(default=True)
    enable_feed = models.BooleanField(default=True)
    enable_notifications = models.BooleanField(default=True)
    enable_text_to_speech = models.BooleanField(default=True)

    # Maintenance Mode
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(default='We are currently under maintenance. Please check back later.')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # Ensure only one instance exists (Singleton pattern)
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get or create site settings singleton"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class ThemeSettings(models.Model):
    """
    Theme/Color settings that admin can change dynamically
    """
    name = models.CharField(max_length=50, default='Default Theme')
    is_active = models.BooleanField(default=True)

    # Primary Colors
    primary_color = models.CharField(max_length=7, default='#4F46E5', help_text='Main brand color (e.g., #4F46E5)')
    primary_hover = models.CharField(max_length=7, default='#4338CA', help_text='Primary hover state')
    primary_light = models.CharField(max_length=7, default='#EEF2FF', help_text='Light variant of primary')

    # Secondary Colors
    secondary_color = models.CharField(max_length=7, default='#10B981', help_text='Secondary accent color')
    secondary_hover = models.CharField(max_length=7, default='#059669')

    # Background Colors
    background_color = models.CharField(max_length=7, default='#F9FAFB', help_text='Main background')
    surface_color = models.CharField(max_length=7, default='#FFFFFF', help_text='Card/surface background')

    # Text Colors
    text_primary = models.CharField(max_length=7, default='#111827', help_text='Primary text color')
    text_secondary = models.CharField(max_length=7, default='#6B7280', help_text='Secondary text color')
    text_muted = models.CharField(max_length=7, default='#9CA3AF', help_text='Muted text color')

    # Status Colors
    success_color = models.CharField(max_length=7, default='#10B981')
    warning_color = models.CharField(max_length=7, default='#F59E0B')
    error_color = models.CharField(max_length=7, default='#EF4444')
    info_color = models.CharField(max_length=7, default='#3B82F6')

    # Navbar & Footer
    navbar_bg = models.CharField(max_length=7, default='#FFFFFF')
    navbar_text = models.CharField(max_length=7, default='#374151')
    footer_bg = models.CharField(max_length=7, default='#1F2937')
    footer_text = models.CharField(max_length=7, default='#F9FAFB')

    # Button Styles
    button_radius = models.CharField(max_length=20, default='0.5rem', help_text='Border radius for buttons')
    card_radius = models.CharField(max_length=20, default='1rem', help_text='Border radius for cards')

    # Shadows
    shadow_sm = models.CharField(max_length=100, default='0 1px 2px 0 rgba(0, 0, 0, 0.05)')
    shadow_md = models.CharField(max_length=100, default='0 4px 6px -1px rgba(0, 0, 0, 0.1)')
    shadow_lg = models.CharField(max_length=100, default='0 10px 15px -3px rgba(0, 0, 0, 0.1)')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Theme Settings'
        verbose_name_plural = 'Theme Settings'

    def __str__(self):
        return f"{self.name} {'(Active)' if self.is_active else ''}"

    def save(self, *args, **kwargs):
        # If this theme is being set as active, deactivate others
        if self.is_active:
            ThemeSettings.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_active_theme(cls):
        """Get the active theme or create default"""
        theme = cls.objects.filter(is_active=True).first()
        if not theme:
            theme, created = cls.objects.get_or_create(
                name='Default Theme',
                defaults={'is_active': True}
            )
        return theme

    def to_css_variables(self):
        """Convert theme settings to CSS variables"""
        return {
            '--primary-color': self.primary_color,
            '--primary-hover': self.primary_hover,
            '--primary-light': self.primary_light,
            '--secondary-color': self.secondary_color,
            '--secondary-hover': self.secondary_hover,
            '--background-color': self.background_color,
            '--surface-color': self.surface_color,
            '--text-primary': self.text_primary,
            '--text-secondary': self.text_secondary,
            '--text-muted': self.text_muted,
            '--success-color': self.success_color,
            '--warning-color': self.warning_color,
            '--error-color': self.error_color,
            '--info-color': self.info_color,
            '--navbar-bg': self.navbar_bg,
            '--navbar-text': self.navbar_text,
            '--footer-bg': self.footer_bg,
            '--footer-text': self.footer_text,
            '--button-radius': self.button_radius,
            '--card-radius': self.card_radius,
            '--shadow-sm': self.shadow_sm,
            '--shadow-md': self.shadow_md,
            '--shadow-lg': self.shadow_lg,
        }


class ActivityLog(models.Model):
    """
    Logs all important activities in the system for admin monitoring
    """
    ACTION_CHOICES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('register', 'User Registration'),
        ('profile_update', 'Profile Update'),
        ('mentor_request', 'Mentor Request'),
        ('session_book', 'Session Booked'),
        ('session_complete', 'Session Completed'),
        ('post_create', 'Post Created'),
        ('message_send', 'Message Sent'),
        ('admin_action', 'Admin Action'),
        ('mentor_facilitator_action', 'Mentor Facilitator Action'),
        ('finance_officer_action', 'Finance Officer Action'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='activity_logs'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    extra_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'

    def __str__(self):
        return f"{self.user} - {self.action} - {self.created_at}"


class Translation(models.Model):
    """
    Custom translations for dynamic content (Kinyarwanda/English)
    """
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('rw', 'Kinyarwanda'),
    ]

    key = models.CharField(max_length=255, help_text='Unique identifier for this text')
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES)
    text = models.TextField()
    context = models.CharField(max_length=100, blank=True, help_text='Where this translation is used')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['key', 'language']
        ordering = ['key', 'language']

    def __str__(self):
        return f"{self.key} ({self.language})"

    @classmethod
    def get_translation(cls, key, language='en', default=''):
        """Get translation for a key in specified language"""
        try:
            return cls.objects.get(key=key, language=language).text
        except cls.DoesNotExist:
            return default


class Testimonial(models.Model):
    """
    Testimonials for the landing page
    """
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100, help_text='e.g., Student, Mentor, Alumni')
    company = models.CharField(max_length=100, blank=True)
    photo = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    content = models.TextField()
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5
    )
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return f"{self.name} - {self.role}"


class FAQ(models.Model):
    """
    Frequently Asked Questions
    """
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question

