"""
Core App URLs
Public pages routing
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('mentors/', views.MentorsListView.as_view(), name='mentors'),
    path('contact/', views.ContactView.as_view(), name='contact'),

    # Static pages
    path('privacy/', views.PrivacyPolicyView.as_view(), name='privacy'),
    path('terms/', views.TermsOfServiceView.as_view(), name='terms'),
    path('cookies/', views.CookiePolicyView.as_view(), name='cookies'),
    path('how-it-works/', views.HowItWorksView.as_view(), name='how_it_works'),
    path('success-stories/', views.SuccessStoriesView.as_view(), name='success_stories'),
    path('mentor-guidelines/', views.MentorGuidelinesView.as_view(), name='mentor_guidelines'),
    path('resources/', views.ResourcesView.as_view(), name='resources'),
    path('community/', views.CommunityView.as_view(), name='community'),

    # Language switching
    path('set-language/', views.set_language, name='set_language'),

    # Accessibility settings
    path('set-accessibility/', views.set_accessibility, name='set_accessibility'),

    # Health check
    path('health/', views.health_check, name='health_check'),
]
