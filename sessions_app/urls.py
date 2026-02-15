from django.urls import path
from . import views

app_name = 'sessions_app'

# Consolidated URL patterns for sessions_app
urlpatterns = [
    # Sessions list/detail
    path('', views.SessionListView.as_view(), name='list'),
    path('<int:pk>/', views.SessionDetailView.as_view(), name='detail'),

    # Booking (CreateView and availability booking)
    path('book/<int:mentor_id>/', views.BookSessionView.as_view(), name='book'),
    path('availability/<int:availability_id>/book/', views.BookAvailabilityView.as_view(), name='book-availability'),

    # Session actions
    path('<int:pk>/cancel/', views.cancel_session, name='cancel'),
    path('<int:pk>/reschedule/', views.RescheduleSessionView.as_view(), name='reschedule'),
    path('<int:pk>/complete/', views.complete_session, name='complete'),
    path('<int:pk>/calendar/', views.session_ics_export, name='session_ics'),

    # Availability (mentor)
    path('availability/', views.AvailabilityListView.as_view(), name='availability'),
    # provide both name variants for compatibility
    path('availability/add/', views.AddAvailabilityView.as_view(), name='add-availability'),
    path('availability/add/', views.AddAvailabilityView.as_view(), name='add_availability'),
    path('availability/<int:pk>/edit/', views.EditAvailabilityView.as_view(), name='edit_availability'),
    path('availability/<int:pk>/delete/', views.delete_availability, name='delete_availability'),

    # Mentor calendar + events JSON endpoint
    path('calendar/<int:mentor_id>/', views.MentorCalendarView.as_view(), name='mentor_calendar'),
    path('mentor/<int:mentor_id>/schedule/', views.MentorScheduleView.as_view(), name='mentor-schedule'),
    path('api/mentor/<int:mentor_id>/events/', views.EventsJsonView.as_view(), name='mentor-events-json'),

    # Mentor session management
    path('mentor/<int:mentor_id>/create-session/', views.MentorCreateSessionView.as_view(), name='mentor-create-session'),
    path('student/schedule/', views.StudentScheduleView.as_view(), name='student-schedule'),
    path('mentor/sessions/', views.MentorSessionsListView.as_view(), name='mentor-sessions'),

    # Approve/reject/start/complete routes
    path('session/<int:session_id>/approve/', views.ApproveSessionView.as_view(), name='approve-session'),
    path('session/<int:session_id>/reject/', views.RejectSessionView.as_view(), name='reject-session'),
    path('session/<int:session_id>/start/', views.StartSessionView.as_view(), name='start-session'),
    path('session/<int:session_id>/complete/', views.CompleteSessionView.as_view(), name='complete-session'),
]
