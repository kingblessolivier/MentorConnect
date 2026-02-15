"""
Dashboard App URLs
"""

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    
    path('', views.DashboardRedirectView.as_view(), name='home'),

    
    path('student/', views.StudentDashboardView.as_view(), name='student_dashboard'),
    path('mentor/', views.MentorDashboardView.as_view(), name='mentor_dashboard'),
    path('admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('finance/', views.FinanceDashboardView.as_view(), name='finance_dashboard'),
    path('mentor-facilitator/', views.MentorFacilitatorDashboardView.as_view(), name='mentor_facilitator_dashboard'),


    path('finance/applications/<int:application_id>/verify/', views.finance_verify_payment, name='finance_verify_payment'),
    path('finance/payments/', views.FinancePaymentsView.as_view(), name='finance_payments'),
    path('finance/reports/', views.FinanceReportsView.as_view(), name='finance_reports'),
    path('finance/export/', views.finance_export, name='finance_export'),

   
    path('subscription/', views.subscription_wizard, name='subscription_wizard'),
    path('subscription/<int:step>/', views.subscription_wizard, name='subscription_wizard_step'),
    path('subscription/payment_proof/upload/', views.upload_payment_proof, name='upload_payment_proof'),
    path('finance/subscription-payments/', views.FinanceSubscriptionPaymentsView.as_view(), name='finance_subscription_payments'),
    path('finance/subscription-payments/<int:pk>/review/', views.finance_subscription_payment_review, name='finance_subscription_payment_review'),
    path('finance/payment-settings/', views.FinancePaymentSettingsView.as_view(), name='finance_payment_settings'),

    # Mentor Facilitator: mentors, assignments, mentorships, disputes, session reports
    path('mentor-facilitator/mentors/', views.MFMentorListView.as_view(), name='mf_mentors'),
    path('mentor-facilitator/mentors/add/', views.MFMentorCreateView.as_view(), name='mf_mentor_add'),
    path('mentor-facilitator/mentors/<int:pk>/edit/', views.MFMentorUpdateView.as_view(), name='mf_mentor_edit'),
    path('mentor-facilitator/assignments/', views.MFAssignmentsView.as_view(), name='mf_assignments'),
    path('mentor-facilitator/mentorships/', views.MFMentorshipsView.as_view(), name='mf_mentorships'),
    path('mentor-facilitator/inactive-mentorships/', views.MFInactiveMentorshipsView.as_view(), name='mf_inactive_mentorships'),
    path('mentor-facilitator/applications/', views.MFApplicationsView.as_view(), name='mf_applications'),
    path('mentor-facilitator/applications/<int:pk>/reassign/', views.mf_reassign_mentor, name='mf_reassign_mentor'),
    path('mentor-facilitator/disputes/', views.MFDisputesView.as_view(), name='mf_disputes'),
    path('mentor-facilitator/disputes/<int:pk>/resolve/', views.mf_dispute_resolve, name='mf_dispute_resolve'),
    path('mentor-facilitator/session-reports/', views.MFSessionReportsView.as_view(), name='mf_session_reports'),
    path('mentor-facilitator/session-reports/<int:pk>/approve/', views.mf_session_report_approve, name='mf_session_report_approve'),
    path('mentor-facilitator/sessions/', views.MFSessionsView.as_view(), name='mf_sessions'),
    path('mentor-facilitator/sessions/create/', views.MFCreateSessionView.as_view(), name='mf_create_session'),
    path('mentor-facilitator/onboarding/', views.MFOnboardingView.as_view(), name='mf_onboarding'),
    path('mentor-facilitator/backup/', views.MFBackupView.as_view(), name='mf_backup'),

    
    path('admin/users/', views.AdminUserListView.as_view(), name='admin_users'),
    path('admin/staff/mentor-facilitator/add/', views.AdminMentorFacilitatorCreateView.as_view(), name='admin_create_mentor_facilitator'),
    path('admin/staff/finance-officer/add/', views.AdminFinanceOfficerCreateView.as_view(), name='admin_create_finance_officer'),
    path('admin/staff/admin/add/', views.AdminAdminCreateView.as_view(), name='admin_create_admin'),
    path('admin/users/<int:pk>/toggle/', views.toggle_user_status, name='toggle_user'),
    path('admin/users/<int:pk>/delete/', views.delete_user, name='delete_user'),

    path('admin/mentors/', views.AdminMentorListView.as_view(), name='admin_mentors'),
    path('admin/mentors/add/', views.AdminMentorCreateView.as_view(), name='admin_mentor_create'),
    path('admin/mentors/<int:pk>/', views.AdminMentorDetailView.as_view(), name='admin_mentor_detail'),
    path('admin/mentors/<int:pk>/assign-facilitator/', views.admin_assign_mentor_to_facilitator, name='admin_assign_mentor_to_facilitator'),
    path('admin/mentors/<int:pk>/unassign-facilitator/<int:facilitator_id>/', views.admin_unassign_mentor_from_facilitator, name='admin_unassign_mentor_from_facilitator'),
    path('admin/mentors/<int:pk>/toggle-verified/', views.toggle_mentor_verified, name='toggle_mentor_verified'),
    path('admin/mentors/<int:pk>/toggle-featured/', views.toggle_mentor_featured, name='toggle_mentor_featured'),

    # Admin Mentorship Requests Management
    path('admin/requests/', views.AdminRequestListView.as_view(), name='admin_requests'),
    path('admin/requests/<int:pk>/', views.AdminRequestDetailView.as_view(), name='admin_request_detail'),

    # Admin Applications Management
    path('admin/applications/', views.AdminApplicationListView.as_view(), name='admin_applications'),
    path('admin/applications/<int:pk>/', views.AdminApplicationDetailView.as_view(), name='admin_application_detail'),
    path('admin/applications/<int:pk>/approve/', views.admin_application_approve, name='admin_application_approve'),
    path('admin/applications/<int:pk>/reject/', views.admin_application_reject, name='admin_application_reject'),

    # Admin Session Management
    path('admin/sessions/', views.AdminSessionListView.as_view(), name='admin_sessions'),

    # Admin Post Management
    path('admin/posts/', views.AdminPostListView.as_view(), name='admin_posts'),
    path('admin/posts/<int:pk>/toggle-status/', views.toggle_post_status, name='toggle_post_status'),
    path('admin/posts/<int:pk>/toggle-pinned/', views.toggle_post_pinned, name='toggle_post_pinned'),
    path('admin/posts/<int:pk>/approve/', views.approve_post, name='approve_post'),
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
