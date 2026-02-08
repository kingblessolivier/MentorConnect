"""
Chat App URLs
"""

from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.ConversationListView.as_view(), name='list'),
    path('conversation/<int:pk>/', views.ConversationDetailView.as_view(), name='conversation'),
    path('start/<int:user_id>/', views.start_conversation, name='start'),
    path('send/<int:conversation_id>/', views.send_message, name='send'),
    path('unread-count/', views.unread_count, name='unread_count'),
    path('message/<int:message_id>/edit/', views.edit_message, name='edit_message'),
    path('message/<int:message_id>/delete/', views.delete_message, name='delete_message'),
    path('search-users/', views.search_users, name='search_users'),
]
