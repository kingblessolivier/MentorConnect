"""
Sessions App URLs
"""

from django.urls import path
from . import views

app_name = 'sessions_app'

urlpatterns = [
    # Sessions
    path('', views.SessionListView.as_view(), name='list'),
    path('<int:pk>/', views.SessionDetailView.as_view(), name='detail'),
    path('book/<int:mentor_id>/', views.BookSessionView.as_view(), name='book'),
    path('<int:pk>/cancel/', views.cancel_session, name='cancel'),
    path('<int:pk>/complete/', views.complete_session, name='complete'),

    # Availability (for mentors)
    path('availability/', views.AvailabilityListView.as_view(), name='availability'),
    path('availability/add/', views.AddAvailabilityView.as_view(), name='add_availability'),
    path('availability/<int:pk>/delete/', views.delete_availability, name='delete_availability'),

    # Calendar view
    path('calendar/<int:mentor_id>/', views.MentorCalendarView.as_view(), name='mentor_calendar'),
]
