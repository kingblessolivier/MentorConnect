"""
Mentorship App URLs
"""

from django.urls import path
from . import views

app_name = 'mentorship'

urlpatterns = [
    # Mentorship requests
    path('request/<int:mentor_id>/', views.CreateMentorshipRequestView.as_view(), name='create_request'),
    path('requests/', views.MentorshipRequestListView.as_view(), name='requests'),
    path('requests/', views.MentorshipRequestListView.as_view(), name='request_list'),  # Alias
    path('requests/<int:pk>/', views.MentorshipRequestDetailView.as_view(), name='request_detail'),
    path('requests/<int:pk>/approve/', views.approve_request, name='approve_request'),
    path('requests/<int:pk>/reject/', views.reject_request, name='reject_request'),
    path('requests/<int:pk>/cancel/', views.cancel_request, name='cancel_request'),

    # Scheduling
    path('requests/<int:pk>/schedule/', views.schedule_session, name='schedule_session'),
    path('requests/<int:pk>/start/', views.start_session, name='start_session'),
    path('requests/<int:pk>/complete/', views.complete_session, name='complete_session'),

    # Reviews
    path('review/<int:mentor_id>/', views.CreateReviewView.as_view(), name='create_review'),
    path('reviews/<int:mentor_id>/', views.MentorReviewsView.as_view(), name='mentor_reviews'),

    # Mentor search
    path('search/', views.MentorSearchView.as_view(), name='search'),

    # Mentor availability calendar (for mentors to manage)
    path('availability/', views.MentorAvailabilityView.as_view(), name='availability'),
    path('availability/add/', views.add_availability, name='add_availability'),

    path('availability/<int:pk>/delete/', views.delete_availability, name='delete_availability'),
    # Slot detail API
    path('api/slot/<int:pk>/', views.api_slot_detail, name='api_slot_detail'),

    # Mentor calendar view (for students to see)
    path('calendar/<int:mentor_id>/', views.MentorCalendarView.as_view(), name='mentor_calendar'),
    path('api/availability/<int:mentor_id>/', views.get_availability_slots, name='api_availability'),

    # New API endpoints
    path('api/search/', views.api_search_mentors, name='api_search'),
    path('api/filters/', views.get_filter_options, name='api_filters'),
]
