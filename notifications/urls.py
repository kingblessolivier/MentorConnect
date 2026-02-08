"""
Notifications App URLs
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='list'),
    path('<int:pk>/read/', views.mark_as_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_read'),
    path('count/', views.unread_count, name='count'),
    path('recent/', views.recent_notifications, name='recent'),
]
