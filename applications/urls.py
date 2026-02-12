"""
Applications App URLs
"""

from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    path('apply/', views.GuestApplicationCreateView.as_view(), name='apply'),
    path('apply/<int:mentor_id>/', views.GuestApplicationCreateView.as_view(), name='apply_to_mentor'),
    path('apply/success/', views.ApplySuccessView.as_view(), name='apply_success'),

    path('invite/<str:token>/', views.register_with_token, name='register_with_token'),

    path('mentor/applications/', views.MentorApplicationListView.as_view(), name='mentor_applications'),
    path('mentor/applications/<int:pk>/', views.MentorApplicationDetailView.as_view(), name='mentor_application_detail'),
    path('mentor/applications/<int:pk>/action/', views.mentor_application_action, name='mentor_application_action'),
]
