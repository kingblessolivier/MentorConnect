"""
Dashboard App URLs
"""

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Generic dashboard redirect
    path('', views.DashboardRedirectView.as_view(), name='home'),

    # Role-specific dashboards
    path('student/', views.StudentDashboardView.as_view(), name='student_dashboard'),
    path('mentor/', views.MentorDashboardView.as_view(), name='mentor_dashboard'),
    path('admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),

    # Admin User Management
    path('admin/users/', views.AdminUserListView.as_view(), name='admin_users'),
    path('admin/users/<int:pk>/toggle/', views.toggle_user_status, name='toggle_user'),
    path('admin/users/<int:pk>/delete/', views.delete_user, name='delete_user'),

    # Admin Mentor Management
    path('admin/mentors/', views.AdminMentorListView.as_view(), name='admin_mentors'),
    path('admin/mentors/add/', views.AdminMentorCreateView.as_view(), name='admin_mentor_create'),
    path('admin/mentors/<int:pk>/', views.AdminMentorDetailView.as_view(), name='admin_mentor_detail'),
    path('admin/mentors/<int:pk>/toggle-verified/', views.toggle_mentor_verified, name='toggle_mentor_verified'),
    path('admin/mentors/<int:pk>/toggle-featured/', views.toggle_mentor_featured, name='toggle_mentor_featured'),

    # Admin Mentorship Requests Management
    path('admin/requests/', views.AdminRequestListView.as_view(), name='admin_requests'),
    path('admin/requests/<int:pk>/', views.AdminRequestDetailView.as_view(), name='admin_request_detail'),

    # Admin Session Management
    path('admin/sessions/', views.AdminSessionListView.as_view(), name='admin_sessions'),

    # Admin Post Management
    path('admin/posts/', views.AdminPostListView.as_view(), name='admin_posts'),
    path('admin/posts/<int:pk>/toggle-status/', views.toggle_post_status, name='toggle_post_status'),
    path('admin/posts/<int:pk>/toggle-pinned/', views.toggle_post_pinned, name='toggle_post_pinned'),
    path('admin/posts/<int:pk>/delete/', views.delete_post, name='delete_post'),

    # Admin Review Management
    path('admin/reviews/', views.AdminReviewListView.as_view(), name='admin_reviews'),
    path('admin/reviews/<int:pk>/delete/', views.delete_review, name='delete_review'),

    # Admin Notification Management
    path('admin/notifications/', views.AdminNotificationListView.as_view(), name='admin_notifications'),

    # Admin Reports & Analytics
    path('admin/reports/', views.AdminReportsView.as_view(), name='admin_reports'),
    path('admin/export/', views.AdminExportDataView.as_view(), name='admin_export'),

    # Admin Settings
    path('admin/theme/', views.AdminThemeView.as_view(), name='admin_theme'),
    path('admin/settings/', views.AdminSettingsView.as_view(), name='admin_settings'),
    path('admin/activity-logs/', views.AdminActivityLogsView.as_view(), name='admin_activity_logs'),
    path('admin/broadcast/', views.AdminBroadcastView.as_view(), name='admin_broadcast'),
]
