"""
Applications App URLs
"""

from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    # Mentor: view mentorship applications where they are the selected mentor
    path('mentor/applications/', views.MentorApplicationListView.as_view(), name='mentor_applications'),
    path('mentor/applications/<int:pk>/', views.MentorApplicationDetailView.as_view(), name='mentor_application_detail'),

    # Logged-in student: pay to submit mentorship application
    path('submit/<int:request_id>/pay/', views.pay_and_submit_application, name='pay_and_submit'),

    # Multi-step application wizard
    path('wizard/', views.application_wizard, name='wizard'),
    path('wizard/<int:step>/', views.application_wizard, name='wizard_step'),
    path('wizard/availability/', views.get_mentor_availability_html, name='wizard_availability'),
    path('track/', views.application_track_status, name='track_status'),
    path('my-applications/', views.StudentApplicationsListView.as_view(), name='my_applications'),
]
