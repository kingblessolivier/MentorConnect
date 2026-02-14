"""
MentorConnect URL Configuration
Main URL routing for the entire project
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # Language switching
    
    # Main app routes (without i18n prefix for simplicity)
    path('', include('core.urls', namespace='core')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('profiles/', include('profiles.urls', namespace='profiles')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('mentorship/', include('mentorship.urls', namespace='mentorship')),
    path('applications/', include('applications.urls', namespace='applications')),
    path('payments/', include('payments.urls', namespace='payments')),
    path('feed/', include('feed.urls', namespace='feed')),
    path('sessions/', include('sessions_app.urls', namespace='sessions_app')),
    path('chat/', include('chat.urls', namespace='chat')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
