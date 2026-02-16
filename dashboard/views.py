
"""
Dashboard App Views
Role-based dashboards for Students, Mentors, and Admins
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, UpdateView, View, CreateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
# ...existing code...

# ...existing code...

class MFApplicationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Mentor Facilitator: view mentorship application details"""
    template_name = 'dashboard/mf_application_detail.html'
    context_object_name = 'application'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_mentor_facilitator

    def get_object(self):
        from applications.models import Application
        return get_object_or_404(Application, pk=self.kwargs['pk'])

    def get_queryset(self):
        from applications.models import Application
        return Application.objects.select_related(
            'applicant', 'selected_mentor', 'selected_availability_slot'
        )

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, UpdateView, View, CreateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.db.models import Count, Avg, Q, Sum, F
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone
from datetime import timedelta
import json
from functools import wraps

from accounts.models import User

from core.models import SiteSettings, ThemeSettings, ActivityLog
from payments.models import PaymentSettings
from .forms import SiteSettingsForm


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user is admin"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_user


class MentorRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user is mentor"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_mentor


class StudentRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user is student"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_student


class FinanceOfficerRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user is finance officer"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_finance_officer


class MentorFacilitatorRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user is mentor facilitator"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_mentor_facilitator


def subscription_required(view_func):
    """Decorator: requires active subscription for student users."""
    from functools import wraps
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        # Only enforce for students
        if hasattr(request.user, 'is_student') and request.user.is_student:
            from payments.models import Subscription
            has_active = Subscription.objects.filter(
                user=request.user, status='active'
            ).exists()
            if not has_active:
                messages.warning(request, 'This feature requires a premium subscription. Subscribe to unlock it!')
                return redirect('dashboard:subscription_wizard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


class DashboardRedirectView(View):
    """Redirects user to their role-specific dashboard or home if not authenticated"""
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('core:home')
        if request.user.is_admin_user:
            return redirect('dashboard:admin_dashboard')
        elif request.user.is_mentor:
            return redirect('dashboard:mentor_dashboard')
        elif request.user.is_mentor_facilitator:
            return redirect('dashboard:mentor_facilitator_dashboard')
        elif request.user.is_finance_officer:
            return redirect('dashboard:finance_dashboard')
        return redirect('dashboard:student_dashboard')


class StudentDashboardView(LoginRequiredMixin, StudentRequiredMixin, TemplateView):
    """Student Dashboard"""
    template_name = 'dashboard/student_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        try:
            from profiles.models import StudentProfile
            profile, _ = StudentProfile.objects.get_or_create(user=user)
            context['profile'] = profile
            context['profile_completion'] = profile.calculate_completion()
        except Exception:
            context['profile'] = None
            context['profile_completion'] = 0

        try:
            from mentorship.models import MentorshipRequest
            context['pending_requests'] = MentorshipRequest.objects.filter(
                student=user, status='pending'
            ).select_related('mentor')[:5]
            context['pending_requests_count'] = MentorshipRequest.objects.filter(
                student=user, status='pending'
            ).count()
            context['approved_sessions'] = MentorshipRequest.objects.filter(
                student=user, status='approved'
            ).select_related('mentor')[:5]
            context['active_mentorships_count'] = MentorshipRequest.objects.filter(
                student=user, status='approved'
            ).count()
        except Exception:
            context['pending_requests'] = []
            context['pending_requests_count'] = 0
            context['approved_sessions'] = []
            context['active_mentorships_count'] = 0

        try:
            from profiles.models import MentorProfile
            context['recommended_mentors'] = MentorProfile.objects.filter(
                is_available=True, user__is_active=True
            ).order_by('-rating')[:6]
        except Exception:
            context['recommended_mentors'] = []

        try:
            from notifications.models import Notification
            context['unread_notifications'] = Notification.objects.filter(
                recipient=user, is_read=False
            ).count()
        except Exception:
            context['unread_notifications'] = 0

        try:
            # Legacy: linked applications with feedback (old GuestApplication flow removed)
            context['linked_applications_with_feedback'] = []
        except Exception:
            context['linked_applications_with_feedback'] = []

        try:
            from payments.models import Subscription, PaymentProof
            active_subscription = Subscription.objects.filter(user=user, status='active').first()
            context['active_subscription'] = active_subscription
            context['has_active_subscription'] = active_subscription and active_subscription.is_active()
            pending_payment_proofs = PaymentProof.objects.filter(user=user, status='pending').count()
            context['pending_payment_proofs'] = pending_payment_proofs
        except Exception:
            context['active_subscription'] = None
            context['has_active_subscription'] = False
            context['pending_payment_proofs'] = 0

        return context


class MentorDashboardView(LoginRequiredMixin, MentorRequiredMixin, TemplateView):
    """Mentor Dashboard"""
    template_name = 'dashboard/mentor_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        try:
            from profiles.models import MentorProfile
            profile, _ = MentorProfile.objects.get_or_create(
                user=user, defaults={'expertise': 'General', 'skills': ''}
            )
            context['profile'] = profile
            context['profile_completion'] = profile.calculate_completion()
        except Exception:
            context['profile'] = None
            context['profile_completion'] = 0

        try:
            from mentorship.models import MentorshipRequest
            from applications.models import Application
            context['pending_requests'] = MentorshipRequest.objects.filter(
                mentor=user, status='pending'
            ).select_related('student')[:10]
            context['total_pending'] = MentorshipRequest.objects.filter(
                mentor=user, status='pending'
            ).count()
            context['mentorship_applications_pending'] = Application.objects.filter(
                selected_mentor=user, status='pending_review'
            ).exclude(status='draft').order_by('-submitted_at')[:5]
            context['total_approved'] = MentorshipRequest.objects.filter(
                mentor=user, status='approved'
            ).count()
            context['total_completed'] = MentorshipRequest.objects.filter(
                mentor=user, status='completed'
            ).count()
        except Exception:
            context['pending_requests'] = []
            context['total_pending'] = 0
            context['total_approved'] = 0
            context['total_completed'] = 0
            context['mentorship_applications_pending'] = []

        try:
            from profiles.models import Follow
            context['followers_count'] = Follow.objects.filter(followed=user).count()
        except Exception:
            context['followers_count'] = 0

        try:
            from notifications.models import Notification
            context['unread_notifications'] = Notification.objects.filter(
                recipient=user, is_read=False
            ).count()
        except Exception:
            context['unread_notifications'] = 0

        return context


class AdminDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Admin Dashboard with comprehensive statistics and charts"""
    template_name = 'dashboard/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # User Statistics
        context['total_users'] = User.objects.count()
        context['total_students'] = User.objects.filter(role='student').count()
        context['total_mentors'] = User.objects.filter(role='mentor').count()
        context['total_admins'] = User.objects.filter(role='admin').count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        context['inactive_users'] = User.objects.filter(is_active=False).count()
        context['new_users_week'] = User.objects.filter(date_joined__gte=week_ago).count()
        context['new_users_month'] = User.objects.filter(date_joined__gte=month_ago).count()

        # User growth data for chart (last 30 days)
        user_growth = User.objects.filter(
            date_joined__gte=month_ago
        ).annotate(
            date=TruncDate('date_joined')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        context['user_growth_labels'] = json.dumps([item['date'].strftime('%b %d') for item in user_growth])
        context['user_growth_data'] = json.dumps([item['count'] for item in user_growth])

        # User distribution by role for pie chart
        context['role_distribution'] = json.dumps([
            context['total_students'],
            context['total_mentors'],
            context['total_admins']
        ])

        # Mentorship Statistics
        try:
            from mentorship.models import MentorshipRequest, Review
            context['total_requests'] = MentorshipRequest.objects.count()
            context['pending_requests'] = MentorshipRequest.objects.filter(status='pending').count()
            context['approved_requests'] = MentorshipRequest.objects.filter(status='approved').count()
            context['completed_requests'] = MentorshipRequest.objects.filter(status='completed').count()
            context['rejected_requests'] = MentorshipRequest.objects.filter(status='rejected').count()

            # Request status distribution for chart
            context['request_status_data'] = json.dumps([
                context['pending_requests'],
                context['approved_requests'],
                MentorshipRequest.objects.filter(status='scheduled').count(),
                MentorshipRequest.objects.filter(status='in_progress').count(),
                context['completed_requests'],
                context['rejected_requests']
            ])

            # Average rating
            avg_rating = Review.objects.aggregate(avg=Avg('rating'))['avg']
            context['average_rating'] = round(avg_rating, 2) if avg_rating else 0
            context['total_reviews'] = Review.objects.count()
        except Exception:
            context['total_requests'] = 0
            context['pending_requests'] = 0
            context['approved_requests'] = 0
            context['completed_requests'] = 0
            context['rejected_requests'] = 0
            context['request_status_data'] = json.dumps([0, 0, 0, 0, 0, 0])
            context['average_rating'] = 0
            context['total_reviews'] = 0

        # Advanced Mentorship Analytics
        try:
            from mentorship.models import MentorshipAnalytics, MentorshipRequest, MentorshipGoal
            from django.db.models import Avg, Q
            
            # Get completed mentorships for analytics
            completed_mentorships = MentorshipRequest.objects.filter(status='completed')
            total_completed = completed_mentorships.count()
            
            if total_completed > 0:
                # Calculate average success metrics from analytics
                analytics_data = MentorshipAnalytics.objects.filter(
                    mentorship__status='completed'
                ).aggregate(
                    avg_success_score=Avg('success_score'),
                    avg_engagement=Avg('engagement_level'),
                    avg_goal_completion=Avg('goal_completion_rate'),
                    avg_attendance=Avg('session_attendance_rate'),
                    avg_student_satisfaction=Avg('student_satisfaction'),
                    avg_mentor_satisfaction=Avg('mentor_satisfaction')
                )
                
                context['avg_success_score'] = round(analytics_data['avg_success_score'] or 0, 1)
                context['avg_engagement_level'] = round(analytics_data['avg_engagement'] or 0, 1)
                context['avg_goal_completion'] = round(analytics_data['avg_goal_completion'] or 0, 1)
                context['avg_session_attendance'] = round(analytics_data['avg_attendance'] or 0, 1)
                context['avg_student_satisfaction'] = round(analytics_data['avg_student_satisfaction'] or 0, 1)
                context['avg_mentor_satisfaction'] = round(analytics_data['avg_mentor_satisfaction'] or 0, 1)
                
                # Calculate time metrics
                time_metrics = []
                for mentorship in completed_mentorships:
                    if mentorship.approved_at and mentorship.created_at:
                        time_to_match = (mentorship.approved_at - mentorship.created_at).total_seconds() / 3600
                        time_metrics.append({'match': time_to_match})
                    if mentorship.scheduled_at and mentorship.approved_at:
                        time_to_schedule = (mentorship.scheduled_at - mentorship.approved_at).total_seconds() / 3600
                        time_metrics.append({'schedule': time_to_schedule})
                    if mentorship.completed_at and mentorship.started_at:
                        time_to_complete = (mentorship.completed_at - mentorship.started_at).total_seconds() / 3600
                        time_metrics.append({'complete': time_to_complete})
                
                if time_metrics:
                    context['avg_time_to_match'] = round(sum(m.get('match', 0) for m in time_metrics) / len([m for m in time_metrics if 'match' in m]), 1) if any('match' in m for m in time_metrics) else 0
                    context['avg_time_to_schedule'] = round(sum(m.get('schedule', 0) for m in time_metrics) / len([m for m in time_metrics if 'schedule' in m]), 1) if any('schedule' in m for m in time_metrics) else 0
                    context['avg_time_to_complete'] = round(sum(m.get('complete', 0) for m in time_metrics) / len([m for m in time_metrics if 'complete' in m]), 1) if any('complete' in m for m in time_metrics) else 0
                else:
                    context['avg_time_to_match'] = 0
                    context['avg_time_to_schedule'] = 0
                    context['avg_time_to_complete'] = 0
                
                # Calculate goal achievement rate
                total_goals = MentorshipGoal.objects.filter(mentorship__status='completed').count()
                completed_goals = MentorshipGoal.objects.filter(mentorship__status='completed', status='completed').count()
                context['goal_achievement_rate'] = round((completed_goals / total_goals * 100) if total_goals > 0 else 0, 1)
                
                # Risk indicators
                at_risk_mentorships = MentorshipAnalytics.objects.filter(
                    intervention_needed=True
                ).count()
                context['at_risk_mentorships'] = at_risk_mentorships
                context['at_risk_percentage'] = round((at_risk_mentorships / total_completed * 100) if total_completed > 0 else 0, 1)
                
                # Success rate (completed vs started)
                total_started = MentorshipRequest.objects.filter(status__in=['in_progress', 'completed']).count()
                context['mentorship_success_rate'] = round((total_completed / total_started * 100) if total_started > 0 else 0, 1)
            else:
                # Default values when no completed mentorships
                context['avg_success_score'] = 0
                context['avg_engagement_level'] = 0
                context['avg_goal_completion'] = 0
                context['avg_session_attendance'] = 0
                context['avg_student_satisfaction'] = 0
                context['avg_mentor_satisfaction'] = 0
                context['avg_time_to_match'] = 0
                context['avg_time_to_schedule'] = 0
                context['avg_time_to_complete'] = 0
                context['goal_achievement_rate'] = 0
                context['at_risk_mentorships'] = 0
                context['at_risk_percentage'] = 0
                context['mentorship_success_rate'] = 0
                
        except Exception as e:
            # Set default values if analytics fail
            context['avg_success_score'] = 0
            context['avg_engagement_level'] = 0
            context['avg_goal_completion'] = 0
            context['avg_session_attendance'] = 0
            context['avg_student_satisfaction'] = 0
            context['avg_mentor_satisfaction'] = 0
            context['avg_time_to_match'] = 0
            context['avg_time_to_schedule'] = 0
            context['avg_time_to_complete'] = 0
            context['goal_achievement_rate'] = 0
            context['at_risk_mentorships'] = 0
            context['at_risk_percentage'] = 0
            context['mentorship_success_rate'] = 0

        # Session Statistics
        try:
            from sessions_app.models import Session
            context['total_sessions'] = Session.objects.count()
            context['scheduled_sessions'] = Session.objects.filter(status='scheduled').count()
            context['completed_sessions'] = Session.objects.filter(status='completed').count()
            context['cancelled_sessions'] = Session.objects.filter(status='cancelled').count()
        except Exception:
            context['total_sessions'] = 0
            context['scheduled_sessions'] = 0
            context['completed_sessions'] = 0
            context['cancelled_sessions'] = 0

        # Feed Statistics
        try:
            from feed.models import Post, Comment, Like
            context['total_posts'] = Post.objects.count()
            context['total_comments'] = Comment.objects.count()
            context['total_likes'] = Like.objects.count()
            context['posts_this_week'] = Post.objects.filter(created_at__gte=week_ago).count()
        except Exception:
            context['total_posts'] = 0
            context['total_comments'] = 0
            context['total_likes'] = 0
            context['posts_this_week'] = 0

        # Notification Statistics
        try:
            from notifications.models import Notification
            context['total_notifications'] = Notification.objects.count()
            context['unread_notifications'] = Notification.objects.filter(is_read=False).count()
        except Exception:
            context['total_notifications'] = 0
            context['unread_notifications'] = 0

        # Top Mentors
        try:
            from profiles.models import MentorProfile
            context['top_mentors'] = MentorProfile.objects.filter(
                user__is_active=True
            ).select_related('user').order_by('-rating', '-total_reviews')[:5]
        except Exception:
            context['top_mentors'] = []

        # Recent Activity
        context['recent_activity'] = ActivityLog.objects.select_related('user').all()[:15]

        # Recent Users
        context['recent_users'] = User.objects.order_by('-date_joined')[:5]

        return context


class AdminUserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """Admin view to list and manage all users"""
    template_name = 'dashboard/admin_users.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) | Q(first_name__icontains=search) | Q(last_name__icontains=search)
            )
        role = self.request.GET.get('role', '')
        if role:
            queryset = queryset.filter(role=role)
        status = self.request.GET.get('status', '')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        return queryset


@login_required
@user_passes_test(lambda u: u.is_admin_user)
def toggle_user_status(request, pk):
    """Toggle user active status"""
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    ActivityLog.objects.create(
        user=request.user, action='admin_action',
        description=f'{"Activated" if user.is_active else "Deactivated"} user {user.email}'
    )
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'is_active': user.is_active})
    messages.success(request, f'User {user.email} has been {"activated" if user.is_active else "deactivated"}.')
    return redirect('dashboard:admin_users')


@login_required
@user_passes_test(lambda u: u.is_admin_user)
def delete_user(request, pk):
    """Delete a user"""
    user = get_object_or_404(User, pk=pk)
    email = user.email
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('dashboard:admin_users')
    user.delete()
    ActivityLog.objects.create(user=request.user, action='admin_action', description=f'Deleted user {email}')
    messages.success(request, f'User {email} has been deleted.')
    return redirect('dashboard:admin_users')


class AdminThemeView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """Admin view to manage theme/color settings"""
    model = ThemeSettings
    template_name = 'dashboard/admin_theme.html'
    fields = [
        'name', 'primary_color', 'primary_hover', 'primary_light',
        'secondary_color', 'secondary_hover', 'background_color',
        'surface_color', 'text_primary', 'text_secondary', 'text_muted',
        'success_color', 'warning_color', 'error_color', 'info_color',
        'navbar_bg', 'navbar_text', 'footer_bg', 'footer_text',
        'button_radius', 'card_radius'
    ]
    success_url = reverse_lazy('dashboard:admin_theme')

    def get_object(self):
        return ThemeSettings.get_active_theme()

    def form_valid(self, form):
        messages.success(self.request, 'Theme settings have been updated!')
        ActivityLog.objects.create(user=self.request.user, action='admin_action', description='Updated theme settings')
        return super().form_valid(form)


class AdminSettingsView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """Admin view to manage site settings"""
    model = SiteSettings
    template_name = 'dashboard/admin_settings.html'
    form_class = SiteSettingsForm
    success_url = reverse_lazy('dashboard:admin_settings')

    def get_object(self):
        return SiteSettings.get_settings()

    def form_valid(self, form):
        # Handle boolean fields: set to False if missing from POST (unchecked)
        boolean_fields = [
            'enable_chat', 'enable_feed', 'enable_notifications', 'enable_text_to_speech', 'maintenance_mode'
        ]
        for field in boolean_fields:
            if field not in self.request.POST:
                form.instance.__setattr__(field, False)
        messages.success(self.request, 'Site settings have been updated!')
        ActivityLog.objects.create(user=self.request.user, action='admin_action', description='Updated site settings')
        return super().form_valid(form)


class AdminActivityLogsView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """View activity logs"""
    model = ActivityLog
    template_name = 'dashboard/admin_activity_logs.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        queryset = ActivityLog.objects.all()
        action = self.request.GET.get('action', '')
        if action:
            queryset = queryset.filter(action=action)
        user_id = self.request.GET.get('user', '')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset


class AdminBroadcastView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Send broadcast notifications to all users"""
    template_name = 'dashboard/admin_broadcast.html'

    def post(self, request):
        title = request.POST.get('title', '')
        message = request.POST.get('message', '')
        target = request.POST.get('target', 'all')

        if not message:
            messages.error(request, 'Message is required.')
            return redirect('dashboard:admin_broadcast')

        try:
            from notifications.models import Notification
            if target == 'students':
                recipients = User.objects.filter(role='student', is_active=True)
            elif target == 'mentors':
                recipients = User.objects.filter(role='mentor', is_active=True)
            else:
                recipients = User.objects.filter(is_active=True)

            for recipient in recipients:
                Notification.objects.create(
                    recipient=recipient, notification_type='system', title=title, message=message
                )

            ActivityLog.objects.create(
                user=request.user, action='admin_action',
                description=f'Sent broadcast to {recipients.count()} users: {title}'
            )
            messages.success(request, f'Broadcast sent to {recipients.count()} users.')
        except Exception as e:
            messages.error(request, f'Error sending broadcast: {str(e)}')

        return redirect('dashboard:admin_broadcast')


# ==================== CONTACT MESSAGES MANAGEMENT ====================

class AdminContactMessagesView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """Admin view to list and manage all contact messages"""
    template_name = 'dashboard/admin_contact_messages.html'
    context_object_name = 'messages_list'
    paginate_by = 20

    def get_queryset(self):
        from .models import ContactMessage
        queryset = ContactMessage.objects.all().order_by('-created_at')

        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(email__icontains=search) |
                Q(subject__icontains=search) | Q(message__icontains=search)
            )

        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import ContactMessage
        context['total_messages'] = ContactMessage.objects.count()
        context['new_messages'] = ContactMessage.objects.filter(status='new').count()
        context['read_messages'] = ContactMessage.objects.filter(status='read').count()
        context['replied_messages'] = ContactMessage.objects.filter(status='replied').count()
        context['closed_messages'] = ContactMessage.objects.filter(status='closed').count()
        return context


@login_required
@user_passes_test(lambda u: u.is_admin_user)
def admin_contact_message_detail(request, pk):
    """View and manage a single contact message"""
    from .models import ContactMessage
    msg = get_object_or_404(ContactMessage, pk=pk)

    # Mark as read on view
    if not msg.is_read:
        msg.mark_as_read()

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'update_status':
            new_status = request.POST.get('status', '')
            if new_status in dict(ContactMessage.STATUS_CHOICES):
                msg.status = new_status
                if new_status == 'replied':
                    msg.replied_at = timezone.now()
                msg.save()
                messages.success(request, f'Status updated to {msg.get_status_display()}.')
        elif action == 'update_notes':
            msg.admin_notes = request.POST.get('admin_notes', '')
            msg.save()
            messages.success(request, 'Admin notes updated.')

        return redirect('dashboard:admin_contact_message_detail', pk=pk)

    return render(request, 'dashboard/admin_contact_message_detail.html', {'msg': msg})


# ==================== MENTOR MANAGEMENT ====================

class AdminMentorListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """Admin view to list and manage all mentors"""
    template_name = 'dashboard/admin_mentors.html'
    context_object_name = 'mentors'
    paginate_by = 20

    def get_queryset(self):
        from profiles.models import MentorProfile
        queryset = MentorProfile.objects.select_related('user').order_by('-created_at')

        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(expertise__icontains=search) |
                Q(company__icontains=search)
            )

        status = self.request.GET.get('status', '')
        if status == 'verified':
            queryset = queryset.filter(is_verified=True)
        elif status == 'unverified':
            queryset = queryset.filter(is_verified=False)
        elif status == 'featured':
            queryset = queryset.filter(is_featured=True)
        elif status == 'available':
            queryset = queryset.filter(is_available=True)
        elif status == 'unavailable':
            queryset = queryset.filter(is_available=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from profiles.models import MentorProfile
        context['total_mentors'] = MentorProfile.objects.count()
        context['verified_mentors'] = MentorProfile.objects.filter(is_verified=True).count()
        context['featured_mentors'] = MentorProfile.objects.filter(is_featured=True).count()
        context['available_mentors'] = MentorProfile.objects.filter(is_available=True).count()
        return context


class AdminMentorCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Admin view to create a new mentor"""
    template_name = 'dashboard/admin_mentor_form.html'
    model = User
    fields = ['email', 'first_name', 'last_name', 'phone']
    success_url = reverse_lazy('dashboard:admin_mentors')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = 'mentor'
        user.set_password('MentorConnect2026!')  # Default password
        user.save()

        # Create mentor profile
        from profiles.models import MentorProfile
        expertise = self.request.POST.get('expertise', 'General')
        skills = self.request.POST.get('skills', '')
        bio = self.request.POST.get('bio', '')

        MentorProfile.objects.create(
            user=user,
            expertise=expertise,
            skills=skills,
            bio=bio,
            is_verified=self.request.POST.get('is_verified') == 'on',
            is_featured=self.request.POST.get('is_featured') == 'on'
        )

        ActivityLog.objects.create(
            user=self.request.user,
            action='admin_action',
            description=f'Created new mentor: {user.email}'
        )
        messages.success(self.request, f'Mentor {user.get_full_name()} created successfully. Default password: MentorConnect2026!')
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


# ==================== ADMIN: CREATE MENTOR FACILITATOR, FINANCE OFFICER & ADMIN ====================

class AdminMentorFacilitatorCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Admin view to create a mentor facilitator (staff role)"""
    template_name = 'dashboard/admin_staff_form.html'
    model = User
    fields = ['email', 'first_name', 'last_name', 'phone']
    success_url = reverse_lazy('dashboard:admin_users')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = User.Role.MENTOR_FACILITATOR
        user.set_password('MentorConnect2026!')
        user.save()

        from mentorship.models import MentorFacilitator
        bio = self.request.POST.get('bio', '')
        MentorFacilitator.objects.get_or_create(
            user=user,
            defaults={'bio': bio}
        )

        ActivityLog.objects.create(
            user=self.request.user,
            action='admin_action',
            description=f'Created mentor facilitator: {user.email}'
        )
        messages.success(self.request, f'Mentor Facilitator {user.get_full_name()} created. Default password: MentorConnect2026!')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['staff_role'] = 'Mentor Facilitator'
        return context


class AdminFinanceOfficerCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Admin view to create a finance officer (staff role)"""
    template_name = 'dashboard/admin_staff_form.html'
    model = User
    fields = ['email', 'first_name', 'last_name', 'phone']
    success_url = reverse_lazy('dashboard:admin_users')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = User.Role.FINANCE_OFFICER
        user.set_password('MentorConnect2026!')
        user.save()

        ActivityLog.objects.create(
            user=self.request.user,
            action='admin_action',
            description=f'Created finance officer: {user.email}'
        )
        messages.success(self.request, f'Finance Officer {user.get_full_name()} created. Default password: MentorConnect2026!')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['staff_role'] = 'Finance Officer'
        return context


class AdminAdminCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Admin view to create an admin (staff role)"""
    template_name = 'dashboard/admin_staff_form.html'
    model = User
    fields = ['email', 'first_name', 'last_name', 'phone']
    success_url = reverse_lazy('dashboard:admin_users')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = User.Role.ADMIN
        user.is_staff = True
        user.is_superuser = True
        user.is_verified = True
        user.email_verified = True
        user.set_password('MentorConnect2026!')
        user.save()

        ActivityLog.objects.create(
            user=self.request.user,
            action='admin_action',
            description=f'Created admin: {user.email}'
        )
        messages.success(self.request, f'Admin {user.get_full_name()} created. Default password: MentorConnect2026!')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['staff_role'] = 'Admin'
        return context


class AdminMentorDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """Admin view to see mentor details"""
    template_name = 'dashboard/admin_mentor_detail.html'
    context_object_name = 'mentor'

    def get_object(self):
        from profiles.models import MentorProfile
        return get_object_or_404(MentorProfile, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mentor = self.object

        from mentorship.models import MentorshipRequest, Review, MentorFacilitator, MentorFacilitatorAssignment
        context['total_requests'] = MentorshipRequest.objects.filter(mentor=mentor.user).count()
        context['pending_requests'] = MentorshipRequest.objects.filter(mentor=mentor.user, status='pending').count()
        context['completed_requests'] = MentorshipRequest.objects.filter(mentor=mentor.user, status='completed').count()
        context['recent_requests'] = MentorshipRequest.objects.filter(mentor=mentor.user).select_related('student')[:10]
        context['reviews'] = Review.objects.filter(mentor=mentor.user).select_related('student')[:10]
        context['facilitators'] = MentorFacilitator.objects.filter(is_active=True).select_related('user')
        context['mentor_facilitator_assignments'] = MentorFacilitatorAssignment.objects.filter(
            mentor=mentor.user
        ).select_related('facilitator__user')

        return context


@login_required
@user_passes_test(lambda u: u.is_admin_user)
def toggle_mentor_verified(request, pk):
    """Toggle mentor verified status"""
    from profiles.models import MentorProfile
    mentor = get_object_or_404(MentorProfile, pk=pk)
    mentor.is_verified = not mentor.is_verified
    mentor.save()

    ActivityLog.objects.create(
        user=request.user,
        action='admin_action',
        description=f'{"Verified" if mentor.is_verified else "Unverified"} mentor {mentor.user.email}'
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'is_verified': mentor.is_verified})
    messages.success(request, f'Mentor {mentor.user.get_full_name()} has been {"verified" if mentor.is_verified else "unverified"}.')
    return redirect('dashboard:admin_mentors')


@login_required
@user_passes_test(lambda u: u.is_admin_user)
def toggle_mentor_featured(request, pk):
    """Toggle mentor featured status"""
    from profiles.models import MentorProfile
    mentor = get_object_or_404(MentorProfile, pk=pk)
    mentor.is_featured = not mentor.is_featured
    mentor.save()

    ActivityLog.objects.create(
        user=request.user,
        action='admin_action',
        description=f'{"Featured" if mentor.is_featured else "Unfeatured"} mentor {mentor.user.email}'
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'is_featured': mentor.is_featured})
    messages.success(request, f'Mentor {mentor.user.get_full_name()} {"is now featured" if mentor.is_featured else "is no longer featured"}.')
    return redirect('dashboard:admin_mentors')


@login_required
@user_passes_test(lambda u: u.is_admin_user)
def admin_assign_mentor_to_facilitator(request, pk):
    """Admin assigns a mentor to a mentor facilitator"""
    from profiles.models import MentorProfile
    from mentorship.models import MentorFacilitator, MentorFacilitatorAssignment

    mentor_profile = get_object_or_404(MentorProfile, pk=pk)
    facilitator_id = request.POST.get('facilitator_id')
    if not facilitator_id:
        messages.error(request, 'Please select a facilitator.')
        return redirect('dashboard:admin_mentor_detail', pk=pk)

    facilitator = get_object_or_404(MentorFacilitator, pk=facilitator_id, is_active=True)
    _, created = MentorFacilitatorAssignment.objects.get_or_create(
        facilitator=facilitator,
        mentor=mentor_profile.user,
        mentorship_request=None,
        defaults={}
    )
    if created:
        messages.success(request, f'{mentor_profile.user.get_full_name()} assigned to {facilitator.user.get_full_name()}.')
    else:
        messages.info(request, f'Mentor is already assigned to this facilitator.')
    return redirect('dashboard:admin_mentor_detail', pk=pk)


@login_required
@user_passes_test(lambda u: u.is_admin_user)
def admin_unassign_mentor_from_facilitator(request, pk, facilitator_id):
    """Admin unassigns a mentor from a mentor facilitator"""
    from profiles.models import MentorProfile
    from mentorship.models import MentorFacilitatorAssignment

    mentor_profile = get_object_or_404(MentorProfile, pk=pk)
    deleted, _ = MentorFacilitatorAssignment.objects.filter(
        mentor=mentor_profile.user,
        facilitator_id=facilitator_id,
        mentorship_request__isnull=True
    ).delete()
    if deleted:
        messages.success(request, 'Mentor unassigned from facilitator.')
    return redirect('dashboard:admin_mentor_detail', pk=pk)


# ==================== MENTORSHIP REQUESTS MANAGEMENT ====================

class AdminRequestListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """Admin view to list all mentorship requests"""
    template_name = 'dashboard/admin_requests.html'
    context_object_name = 'requests'
    paginate_by = 20

    def get_queryset(self):
        from mentorship.models import MentorshipRequest
        queryset = MentorshipRequest.objects.select_related('student', 'mentor').order_by('-created_at')

        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(student__email__icontains=search) |
                Q(mentor__email__icontains=search) |
                Q(subject__icontains=search)
            )

        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from mentorship.models import MentorshipRequest
        context['total_requests'] = MentorshipRequest.objects.count()
        context['pending_count'] = MentorshipRequest.objects.filter(status='pending').count()
        context['approved_count'] = MentorshipRequest.objects.filter(status='approved').count()
        context['completed_count'] = MentorshipRequest.objects.filter(status='completed').count()
        context['rejected_count'] = MentorshipRequest.objects.filter(status='rejected').count()
        return context


class AdminRequestDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """Admin view to see request details"""
    template_name = 'dashboard/admin_request_detail.html'
    context_object_name = 'mentorship_request'

    def get_object(self):
        from mentorship.models import MentorshipRequest
        return get_object_or_404(MentorshipRequest, pk=self.kwargs['pk'])


# ==================== FINANCE OFFICER DASHBOARD & PAYMENT VERIFICATION ====================

class FinanceDashboardView(LoginRequiredMixin, FinanceOfficerRequiredMixin, TemplateView):
    """Finance officer dashboard: applications pending payment verification"""
    template_name = 'dashboard/finance_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from applications.models import Application, Payment
        from payments.models import PaymentProof

        context['pending_finance'] = Application.objects.filter(
            status='pending_finance'
        ).select_related('applicant', 'mentorship_request__mentor', 'mentorship_request__student', 'selected_mentor').order_by('-submitted_at')[:20]
        context['pending_finance_count'] = Application.objects.filter(status='pending_finance').count()
        context['recent_verified'] = Payment.objects.filter(
            verified=True
        ).select_related('application', 'verified_by').order_by('-verified_at')[:10]
        context['total_verified_count'] = Payment.objects.filter(verified=True).count()
        # Subscription payment proofs
        context['pending_subscription'] = PaymentProof.objects.filter(
            status='pending', payment_type='subscription'
        ).select_related('user').order_by('-submitted_at')[:10]
        context['pending_subscription_count'] = PaymentProof.objects.filter(status='pending', payment_type='subscription').count()
        return context


@login_required
@user_passes_test(lambda u: u.is_finance_officer)
def finance_verify_payment(request, application_id):
    """Finance officer verifies or rejects a payment for an application"""
    from applications.models import Application, Payment, ActivityLog as AppActivityLog
    from django.contrib.contenttypes.models import ContentType

    application = get_object_or_404(Application, pk=application_id, status='pending_finance')
    payment = application.payments.filter(verified=False).order_by('-submitted_at').first()

    if request.method == 'POST':
        print('DEBUG: finance_verify_payment POST received, action =', request.POST.get('action'))
        action = request.POST.get('action')  # 'verify' or 'reject'
        ct = ContentType.objects.get_for_model(Application)
        if action == 'verify':
            if not payment:
                messages.error(request, 'No payment record found for this application. Cannot verify.')
                return redirect('dashboard:finance_verify_payment', application_id=application_id)
            else:
                payment.verified = True
                payment.verified_at = timezone.now()
                payment.verified_by = request.user
                payment.save()
                application.status = 'pending_review'
                application.save(update_fields=['status'])
                AppActivityLog.objects.create(
                    content_type=ct,
                    object_id=application.id,
                    action_type='payment_verified',
                    new_status='pending_review',
                    details=f'Payment {payment.transaction_code} verified by {request.user.email}',
                    performed_by=request.user,
                )
                ActivityLog.objects.create(
                    user=request.user,
                    action='finance_officer_action',
                    description=f'Payment verified for application {application.tracking_code}'
                )
                # Notify student
                try:
                    from notifications.models import Notification
                    student = application.applicant
                    if student:
                        Notification.objects.create(
                            recipient=student,
                            sender=request.user,
                            notification_type='request_approved',
                            title='Payment approved',
                            message=f'Your payment for application {application.tracking_code} has been verified. Your application is now pending mentor review.'
                        )
                except Exception:
                    pass
                messages.success(request, f'Payment verified. Application {application.tracking_code} is now pending mentor review.')
        elif action == 'reject':
            application.status = 'finance_rejected'
            application.save(update_fields=['status'])
            reason = request.POST.get('reason', 'Payment rejected.')
            AppActivityLog.objects.create(
                content_type=ct,
                object_id=application.id,
                action_type='status_change',
                previous_status='pending_finance',
                new_status='finance_rejected',
                details=reason,
                performed_by=request.user,
            )
            ActivityLog.objects.create(
                user=request.user,
                action='finance_officer_action',
                description=f'Payment rejected for application {application.tracking_code}'
            )
            # Notify student
            try:
                from notifications.models import Notification
                student = application.applicant
                if student:
                    Notification.objects.create(
                        recipient=student,
                        sender=request.user,
                        notification_type='request_rejected',
                        title='Payment rejected',
                        message=f'Your payment for application {application.tracking_code} was rejected. Reason: {reason}'
                    )
            except Exception:
                pass
            messages.info(request, f'Application {application.tracking_code} rejected.')
        return redirect('dashboard:finance_dashboard')

    return render(request, 'dashboard/finance_verify_payment.html', {
        'application': application,
        'payment': payment,
    })


# ==================== MENTOR FACILITATOR DASHBOARD ====================

class MentorFacilitatorDashboardView(LoginRequiredMixin, MentorFacilitatorRequiredMixin, TemplateView):
    """Mentor facilitator dashboard: assignments, disputes, session reports"""
    template_name = 'dashboard/mentor_facilitator_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from mentorship.models import MentorFacilitator, Dispute, MentorFacilitatorAssignment

        try:
            facilitator = self.request.user.mentor_facilitator_profile
        except Exception:
            facilitator = None

        context['facilitator'] = facilitator
        if facilitator:
            context['assignments'] = MentorFacilitatorAssignment.objects.filter(
                facilitator=facilitator
            ).select_related('mentor', 'mentorship_request__student', 'mentorship_request__mentor')[:15]
            context['open_disputes'] = Dispute.objects.filter(
                status__in=['open', 'under_review'],
                facilitator=facilitator
            ).select_related('mentorship_request', 'reported_by')[:10]
        else:
            context['assignments'] = []
            context['open_disputes'] = []

        # Stats for dashboard
        if facilitator:
            from mentorship.models import MentorshipRequest, SessionReport
            from applications.models import Application
            from profiles.models import MentorProfile
            assigned_mentor_ids = list(MentorFacilitatorAssignment.objects.filter(
                facilitator=facilitator
            ).exclude(mentor__isnull=True).values_list('mentor_id', flat=True))
            context['assigned_mentors_count'] = len(set(assigned_mentor_ids))
            context['active_mentorships_count'] = MentorshipRequest.objects.filter(
                status__in=['approved', 'scheduled', 'in_progress'],
                mentor_id__in=assigned_mentor_ids
            ).count() if assigned_mentor_ids else 0
            context['disputes_count'] = Dispute.objects.filter(
                facilitator=facilitator,
                status__in=['open', 'under_review']
            ).count()
            context['session_reports_count'] = SessionReport.objects.filter(
                mentorship_request__mentor_id__in=assigned_mentor_ids
            ).count() if assigned_mentor_ids else 0

            # Pending requests for assigned mentors (same as mentor dashboard)
            context['pending_requests'] = MentorshipRequest.objects.filter(
                mentor_id__in=assigned_mentor_ids, status='pending'
            ).select_related('student', 'mentor')[:10] if assigned_mentor_ids else []
            context['total_pending_requests'] = MentorshipRequest.objects.filter(
                mentor_id__in=assigned_mentor_ids, status='pending'
            ).count() if assigned_mentor_ids else 0

            # Pending applications for assigned mentors
            context['pending_applications'] = Application.objects.filter(
                selected_mentor_id__in=assigned_mentor_ids,
                status='pending_review'
            ).exclude(status='draft').select_related(
                'applicant', 'selected_mentor'
            ).order_by('-submitted_at')[:5] if assigned_mentor_ids else []
            context['total_pending_applications'] = Application.objects.filter(
                selected_mentor_id__in=assigned_mentor_ids,
                status='pending_review'
            ).exclude(status='draft').count() if assigned_mentor_ids else 0

            # Completed mentorships count
            context['completed_mentorships_count'] = MentorshipRequest.objects.filter(
                mentor_id__in=assigned_mentor_ids, status='completed'
            ).count() if assigned_mentor_ids else 0

            # Mentor profiles for quick overview
            context['mentor_profiles'] = MentorProfile.objects.filter(
                user_id__in=assigned_mentor_ids
            ).select_related('user')[:10] if assigned_mentor_ids else []
        else:
            context['assigned_mentors_count'] = 0
            context['active_mentorships_count'] = 0
            context['disputes_count'] = 0
            context['session_reports_count'] = 0
            context['pending_requests'] = []
            context['total_pending_requests'] = 0
            context['pending_applications'] = []
            context['total_pending_applications'] = 0
            context['completed_mentorships_count'] = 0
            context['mentor_profiles'] = []

        return context


# ==================== MENTOR FACILITATOR: MENTORS, ASSIGNMENTS, DISPUTES ====================

class MFMentorListView(LoginRequiredMixin, MentorFacilitatorRequiredMixin, ListView):
    """Mentor Facilitator: list mentors (can add/edit)"""
    template_name = 'dashboard/mf_mentors.html'
    context_object_name = 'mentors'
    paginate_by = 20

    def get_queryset(self):
        from profiles.models import MentorProfile
        qs = MentorProfile.objects.select_related('user').order_by('-created_at')
        search = self.request.GET.get('search', '')
        if search:
            qs = qs.filter(
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(expertise__icontains=search)
            )
        status = self.request.GET.get('status', '')
        if status == 'available':
            qs = qs.filter(is_available=True)
        elif status == 'unavailable':
            qs = qs.filter(is_available=False)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from profiles.models import MentorProfile
        context['total_mentors'] = MentorProfile.objects.count()
        return context


class MFMentorCreateView(LoginRequiredMixin, MentorFacilitatorRequiredMixin, CreateView):
    """Mentor Facilitator: add new mentor"""
    template_name = 'dashboard/admin_mentor_form.html'
    model = User
    fields = ['email', 'first_name', 'last_name', 'phone']
    success_url = reverse_lazy('dashboard:mf_mentors')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = 'mentor'
        user.set_password('MentorConnect2026!')
        user.save()
        from profiles.models import MentorProfile
        MentorProfile.objects.create(
            user=user,
            expertise=self.request.POST.get('expertise', 'General'),
            skills=self.request.POST.get('skills', ''),
            bio=self.request.POST.get('bio', ''),
        )
        ActivityLog.objects.create(
            user=self.request.user,
            action='mentor_facilitator_action',
            description=f'Added mentor: {user.email}'
        )
        messages.success(self.request, f'Mentor {user.get_full_name()} added. Default password: MentorConnect2026!')
        return redirect(self.success_url)


class MFMentorUpdateView(LoginRequiredMixin, MentorFacilitatorRequiredMixin, UpdateView):
    """Mentor Facilitator: update mentor profile (skills, availability, etc.)"""
    template_name = 'dashboard/mf_mentor_edit.html'
    model = User
    fields = ['first_name', 'last_name', 'phone']
    context_object_name = 'mentor_user'
    success_url = reverse_lazy('dashboard:mf_mentors')

    def get_queryset(self):
        return User.objects.filter(role='mentor')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from profiles.models import MentorProfile
        try:
            context['profile'] = MentorProfile.objects.get(user=self.object)
        except MentorProfile.DoesNotExist:
            context['profile'] = None
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        section = request.POST.get('section', 'all')
        from profiles.models import MentorProfile
        profile, _ = MentorProfile.objects.get_or_create(
            user=self.object,
            defaults={'expertise': 'General', 'skills': ''}
        )

        if section == 'basic':
            self.object.first_name = request.POST.get('first_name', self.object.first_name)
            self.object.last_name = request.POST.get('last_name', self.object.last_name)
            self.object.phone = request.POST.get('phone', '')
            self.object.save()
            profile.headline = request.POST.get('headline', '')
            profile.job_title = request.POST.get('job_title', '')
            profile.company = request.POST.get('company', '')
            exp = request.POST.get('experience_years')
            profile.experience_years = int(exp) if exp else None
            profile.save()
            messages.success(request, 'Basic information updated!')

        elif section == 'about':
            profile.bio = request.POST.get('bio', '')
            profile.save()
            messages.success(request, 'Bio updated!')

        elif section == 'skills':
            profile.expertise = request.POST.get('expertise', '')
            profile.skills = request.POST.get('skills', '')
            profile.save()
            messages.success(request, 'Expertise & skills updated!')

        elif section == 'availability':
            profile.is_available = request.POST.get('is_available') == 'on'
            duration = request.POST.get('session_duration')
            profile.session_duration = int(duration) if duration else 60
            max_mentees = request.POST.get('max_mentees')
            profile.max_mentees = int(max_mentees) if max_mentees else 5
            rate = request.POST.get('hourly_rate')
            profile.hourly_rate = float(rate) if rate else None
            profile.save()
            messages.success(request, 'Availability settings updated!')

        elif section == 'location':
            profile.city = request.POST.get('city', '')
            profile.country = request.POST.get('country', 'Rwanda')
            profile.workplace_address = request.POST.get('workplace_address', '')
            profile.diploma = request.POST.get('diploma', '')
            profile.educational_institution = request.POST.get('educational_institution', '')
            min_days = request.POST.get('min_internship_days')
            profile.min_internship_days = int(min_days) if min_days else 1
            max_days = request.POST.get('max_internship_days')
            profile.max_internship_days = int(max_days) if max_days else 5
            profile.accepts_in_person = request.POST.get('accepts_in_person') == 'true'
            profile.accepts_virtual = request.POST.get('accepts_virtual') == 'true'
            profile.save()
            messages.success(request, 'Location & internship settings updated!')

        elif section == 'social':
            profile.linkedin_url = request.POST.get('linkedin_url', '')
            profile.twitter_url = request.POST.get('twitter_url', '')
            profile.github_url = request.POST.get('github_url', '')
            profile.website_url = request.POST.get('website_url', '')
            profile.save()
            messages.success(request, 'Social links updated!')

        else:
            return super().post(request, *args, **kwargs)

        ActivityLog.objects.create(
            user=request.user,
            action='mentor_facilitator_action',
            description=f'Updated mentor profile ({section}): {self.object.get_full_name()}'
        )
        return redirect('dashboard:mf_mentor_edit', pk=self.object.pk)


class MFAssignmentsView(LoginRequiredMixin, MentorFacilitatorRequiredMixin, ListView):
    """Mentor Facilitator: assigned mentors and students"""
    template_name = 'dashboard/mf_assignments.html'
    context_object_name = 'assignments'
    paginate_by = 20

    def get_queryset(self):
        from mentorship.models import MentorFacilitatorAssignment
        try:
            facilitator = self.request.user.mentor_facilitator_profile
            return MentorFacilitatorAssignment.objects.filter(
                facilitator=facilitator
            ).select_related('mentor', 'mentorship_request__student', 'mentorship_request__mentor').order_by('-assigned_at')
        except Exception:
            from mentorship.models import MentorFacilitatorAssignment
            return MentorFacilitatorAssignment.objects.none()


class MFMentorshipsView(LoginRequiredMixin, MentorFacilitatorRequiredMixin, ListView):
    """Mentor Facilitator: active mentorships of assigned mentors"""
    template_name = 'dashboard/mf_mentorships.html'
    context_object_name = 'mentorships'
    paginate_by = 20

    def get_queryset(self):
        from mentorship.models import MentorFacilitatorAssignment, MentorshipRequest
        try:
            facilitator = self.request.user.mentor_facilitator_profile
            mentor_ids = list(MentorFacilitatorAssignment.objects.filter(
                facilitator=facilitator
            ).exclude(mentor__isnull=True).values_list('mentor_id', flat=True))
            return MentorshipRequest.objects.filter(
                mentor_id__in=mentor_ids,
                status__in=['approved', 'scheduled', 'in_progress']
            ).select_related('student', 'mentor').order_by('-updated_at')
        except Exception:
            from mentorship.models import MentorshipRequest
            return MentorshipRequest.objects.none()


class MFInactiveMentorshipsView(LoginRequiredMixin, MentorFacilitatorRequiredMixin, ListView):
    """Mentor Facilitator: flag inactive mentorships (no session in last 30 days)"""
    template_name = 'dashboard/mf_inactive_mentorships.html'
    context_object_name = 'mentorships'
    paginate_by = 20

    def get_queryset(self):
        from mentorship.models import MentorFacilitatorAssignment, MentorshipRequest, SessionReport
        from django.utils import timezone
        from datetime import timedelta
        try:
            facilitator = self.request.user.mentor_facilitator_profile
            mentor_ids = list(MentorFacilitatorAssignment.objects.filter(
                facilitator=facilitator
            ).exclude(mentor__isnull=True).values_list('mentor_id', flat=True))
            # Get mentorships that are active (approved, scheduled, in_progress)
            active_mentorships = MentorshipRequest.objects.filter(
                mentor_id__in=mentor_ids,
                status__in=['approved', 'scheduled', 'in_progress']
            ).select_related('student', 'mentor')
            # Filter those with no session report in last 30 days
            cutoff = timezone.now() - timedelta(days=30)
            inactive = []
            for mr in active_mentorships:
                has_recent = SessionReport.objects.filter(
                    mentorship_request=mr,
                    session_date__gte=cutoff
                ).exists()
                if not has_recent:
                    inactive.append(mr.id)
            # Return the filtered queryset
            return MentorshipRequest.objects.filter(id__in=inactive).select_related('student', 'mentor').order_by('-updated_at')
        except Exception:
            from mentorship.models import MentorshipRequest
            return MentorshipRequest.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['inactive_count'] = self.get_queryset().count()
        return context


class MFApplicationsView(LoginRequiredMixin, MentorFacilitatorRequiredMixin, ListView):
    """Mentor Facilitator: monitor applications for assigned mentors"""
    template_name = 'dashboard/mf_applications.html'
    context_object_name = 'applications'
    paginate_by = 20

    def get_queryset(self):
        from applications.models import Application
        from mentorship.models import MentorFacilitatorAssignment
        try:
            facilitator = self.request.user.mentor_facilitator_profile
            mentor_ids = list(MentorFacilitatorAssignment.objects.filter(
                facilitator=facilitator
            ).exclude(mentor__isnull=True).values_list('mentor_id', flat=True))
            qs = Application.objects.exclude(status='draft').filter(
                selected_mentor_id__in=mentor_ids
            ).select_related('applicant', 'selected_mentor', 'selected_availability_slot').order_by('-submitted_at')
            # Filter by status
            status = self.request.GET.get('status', '')
            if status:
                qs = qs.filter(status=status)
            # Filter by minor
            minor = self.request.GET.get('minor', '')
            if minor == 'yes':
                qs = qs.filter(is_minor=True)
            elif minor == 'no':
                qs = qs.filter(is_minor=False)
            # Search
            search = self.request.GET.get('search', '')
            if search:
                qs = qs.filter(
                    Q(name__icontains=search) |
                    Q(email__icontains=search) |
                    Q(tracking_code__icontains=search) |
                    Q(school__icontains=search)
                )
            return qs
        except Exception:
            from applications.models import Application
            return Application.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from applications.models import Application
        from mentorship.models import MentorFacilitatorAssignment
        try:
            facilitator = self.request.user.mentor_facilitator_profile
            mentor_ids = list(MentorFacilitatorAssignment.objects.filter(
                facilitator=facilitator
            ).exclude(mentor__isnull=True).values_list('mentor_id', flat=True))
            qs = Application.objects.exclude(status='draft').filter(selected_mentor_id__in=mentor_ids)
            context['total_applications'] = qs.count()
            context['pending_count'] = qs.filter(status='pending_review').count()
            context['approved_count'] = qs.filter(status__in=['approved', 'enrolled']).count()
            context['rejected_count'] = qs.filter(status__in=['finance_rejected', 'review_rejected']).count()
            context['minor_count'] = qs.filter(is_minor=True).count()
        except Exception:
            context['total_applications'] = 0
            context['pending_count'] = 0
            context['approved_count'] = 0
            context['rejected_count'] = 0
            context['minor_count'] = 0
        return context


@login_required
@user_passes_test(lambda u: u.is_mentor_facilitator)
def mf_reassign_mentor(request, pk):
    """Mentor Facilitator: reassign application to another mentor"""
    from applications.models import Application
    from mentorship.models import MentorFacilitatorAssignment
    from core.models import ActivityLog
    application = get_object_or_404(Application, pk=pk)
    # Ensure facilitator is assigned to the current mentor
    try:
        facilitator = request.user.mentor_facilitator_profile
        mentor_ids = list(MentorFacilitatorAssignment.objects.filter(
            facilitator=facilitator
        ).exclude(mentor__isnull=True).values_list('mentor_id', flat=True))
        if application.selected_mentor_id not in mentor_ids:
            messages.error(request, 'You are not assigned to this mentor.')
            return redirect('dashboard:mf_applications')
    except Exception:
        messages.error(request, 'Facilitator profile not found.')
        return redirect('dashboard:mf_applications')
    
    if request.method == 'POST':
        new_mentor_id = request.POST.get('new_mentor')
        if not new_mentor_id:
            messages.error(request, 'Please select a mentor.')
            return redirect('dashboard:mf_applications')
        # Ensure new mentor is also assigned to facilitator
        if int(new_mentor_id) not in mentor_ids:
            messages.error(request, 'You cannot assign to a mentor not under your supervision.')
            return redirect('dashboard:mf_applications')
        old_mentor = application.selected_mentor
        application.selected_mentor_id = new_mentor_id
        application.save()
        ActivityLog.objects.create(
            user=request.user,
            action='mentor_facilitator_action',
            description=f'Reassigned application {application.tracking_code} from {old_mentor.get_full_name()} to {application.selected_mentor.get_full_name()}'
        )
        messages.success(request, 'Mentor reassigned successfully.')
        return redirect('dashboard:mf_applications')
    # GET: show form with mentor choices
    from accounts.models import User
    mentors = User.objects.filter(id__in=mentor_ids, role='mentor', is_active=True)
    return render(request, 'dashboard/mf_reassign_mentor.html', {
        'application': application,
        'mentors': mentors,
    })


class MFDisputesView(LoginRequiredMixin, MentorFacilitatorRequiredMixin, ListView):
    """Mentor Facilitator: dispute resolution queue"""
    template_name = 'dashboard/mf_disputes.html'
    context_object_name = 'disputes'
    paginate_by = 20

    def get_queryset(self):
        from mentorship.models import Dispute
        try:
            facilitator = self.request.user.mentor_facilitator_profile
            return Dispute.objects.filter(facilitator=facilitator).select_related(
                'mentorship_request__student', 'mentorship_request__mentor', 'reported_by'
            ).order_by('-created_at')
        except Exception:
            return Dispute.objects.none()


@login_required
@user_passes_test(lambda u: u.is_mentor_facilitator)
def mf_dispute_resolve(request, pk):
    """Mentor Facilitator: resolve a dispute"""
    from mentorship.models import Dispute
    dispute = get_object_or_404(Dispute, pk=pk)
    try:
        if dispute.facilitator != request.user.mentor_facilitator_profile:
            return redirect('dashboard:mf_disputes')
    except Exception:
        return redirect('dashboard:mf_disputes')
    if request.method == 'POST':
        status = request.POST.get('status', 'resolved')
        notes = request.POST.get('resolution_notes', '')
        dispute.status = status
        dispute.resolution_notes = notes
        dispute.save()
        ActivityLog.objects.create(
            user=request.user,
            action='mentor_facilitator_action',
            description=f'Resolved dispute #{pk}: {status}'
        )
        # Notify admin if escalated
        if status == 'escalated':
            from notifications.models import Notification
            from accounts.models import User
            admin_users = User.objects.filter(role='admin', is_active=True)
            for admin in admin_users:
                Notification.objects.create(
                    recipient=admin,
                    sender=request.user,
                    notification_type='dispute_escalated',
                    message=f'Dispute #{pk} has been escalated by {request.user.get_full_name()}.'
                )
        messages.success(request, 'Dispute updated.')
        return redirect('dashboard:mf_disputes')
    return render(request, 'dashboard/mf_dispute_resolve.html', {'dispute': dispute})


class MFSessionReportsView(LoginRequiredMixin, MentorFacilitatorRequiredMixin, ListView):
    """Mentor Facilitator: pending session reports"""
    template_name = 'dashboard/mf_session_reports.html'
    context_object_name = 'reports'
    paginate_by = 20

    def get_queryset(self):
        from mentorship.models import MentorFacilitatorAssignment, SessionReport
        try:
            facilitator = self.request.user.mentor_facilitator_profile
            mentor_ids = list(MentorFacilitatorAssignment.objects.filter(
                facilitator=facilitator
            ).exclude(mentor__isnull=True).values_list('mentor_id', flat=True))
            return SessionReport.objects.filter(
                mentorship_request__mentor_id__in=mentor_ids
            ).select_related('mentorship_request__student', 'mentorship_request__mentor').order_by('-session_date', '-session_time')
        except Exception:
            from mentorship.models import SessionReport
            return SessionReport.objects.none()


@login_required
@user_passes_test(lambda u: u.is_mentor_facilitator)
def mf_session_report_approve(request, pk):
    """Mentor Facilitator: approve a session report"""
    from mentorship.models import SessionReport, MentorFacilitatorAssignment
    from core.models import ActivityLog
    report = get_object_or_404(SessionReport, pk=pk)
    # Ensure facilitator is assigned to the mentor of this report
    try:
        facilitator = request.user.mentor_facilitator_profile
        mentor_ids = list(MentorFacilitatorAssignment.objects.filter(
            facilitator=facilitator
        ).exclude(mentor__isnull=True).values_list('mentor_id', flat=True))
        if report.mentorship_request.mentor_id not in mentor_ids:
            messages.error(request, 'You are not assigned to this mentor.')
            return redirect('dashboard:mf_session_reports')
    except Exception:
        messages.error(request, 'Facilitator profile not found.')
        return redirect('dashboard:mf_session_reports')
    
    if request.method == 'POST':
        report.approved_by_facilitator = True
        report.save()
        ActivityLog.objects.create(
            user=request.user,
            action='mentor_facilitator_action',
            description=f'Approved session report #{report.pk} for mentorship {report.mentorship_request.pk}'
        )
        messages.success(request, 'Session report approved.')
        return redirect('dashboard:mf_session_reports')
    # If GET, redirect back
    return redirect('dashboard:mf_session_reports')


class MFSessionsView(LoginRequiredMixin, MentorFacilitatorRequiredMixin, ListView):
    """Mentor Facilitator: view sessions for assigned mentors (calendar/list)"""
    template_name = 'dashboard/mf_sessions.html'
    context_object_name = 'sessions'
    paginate_by = 30

    def get_queryset(self):
        from sessions_app.models import Session
        from mentorship.models import MentorFacilitatorAssignment
        try:
            facilitator = self.request.user.mentor_facilitator_profile
            mentor_ids = list(MentorFacilitatorAssignment.objects.filter(
                facilitator=facilitator
            ).exclude(mentor__isnull=True).values_list('mentor_id', flat=True))
            qs = Session.objects.filter(mentor_id__in=mentor_ids).select_related(
                'mentor', 'student', 'availability'
            ).order_by('-start')
            # Filter by status
            status = self.request.GET.get('status', '')
            if status:
                qs = qs.filter(status=status)
            # Filter by date range
            date_from = self.request.GET.get('date_from', '')
            date_to = self.request.GET.get('date_to', '')
            if date_from:
                qs = qs.filter(start__date__gte=date_from)
            if date_to:
                qs = qs.filter(start__date__lte=date_to)
            return qs
        except Exception:
            from sessions_app.models import Session
            return Session.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from sessions_app.models import Session
        from mentorship.models import MentorFacilitatorAssignment
        try:
            facilitator = self.request.user.mentor_facilitator_profile
            mentor_ids = list(MentorFacilitatorAssignment.objects.filter(
                facilitator=facilitator
            ).exclude(mentor__isnull=True).values_list('mentor_id', flat=True))
            context['total_sessions'] = Session.objects.filter(mentor_id__in=mentor_ids).count()
            context['upcoming_sessions'] = Session.objects.filter(
                mentor_id__in=mentor_ids, start__gte=timezone.now()
            ).count()
            context['past_sessions'] = Session.objects.filter(
                mentor_id__in=mentor_ids, start__lt=timezone.now()
            ).count()
        except Exception:
            context['total_sessions'] = 0
            context['upcoming_sessions'] = 0
            context['past_sessions'] = 0
        return context


class MFCreateSessionView(LoginRequiredMixin, MentorFacilitatorRequiredMixin, View):
    """Mentor Facilitator: create a session for an assigned mentor"""
    template_name = 'sessions_app/create_session.html'

    def get(self, request):
        from sessions_app.forms import SessionCreateForm
        from mentorship.models import MentorFacilitatorAssignment
        try:
            facilitator = request.user.mentor_facilitator_profile
            mentor_ids = list(MentorFacilitatorAssignment.objects.filter(
                facilitator=facilitator
            ).exclude(mentor__isnull=True).values_list('mentor_id', flat=True))
            from accounts.models import User
            mentors = User.objects.filter(id__in=mentor_ids, role='mentor')
        except Exception:
            mentors = User.objects.none()
        form = SessionCreateForm()
        # Limit student queryset to all students? We'll keep default.
        return render(request, self.template_name, {'form': form, 'mentors': mentors})

    def post(self, request):
        from sessions_app.forms import SessionCreateForm
        from mentorship.models import MentorFacilitatorAssignment
        try:
            facilitator = request.user.mentor_facilitator_profile
            mentor_ids = list(MentorFacilitatorAssignment.objects.filter(
                facilitator=facilitator
            ).exclude(mentor__isnull=True).values_list('mentor_id', flat=True))
        except Exception:
            mentor_ids = []
        form = SessionCreateForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            # Ensure selected mentor is assigned to facilitator
            if session.mentor_id not in mentor_ids:
                messages.error(request, 'You can only create sessions for assigned mentors.')
                return render(request, self.template_name, {'form': form})
            session.status = 'approved'
            session.save()
            # Notify student
            try:
                from notifications.models import Notification
                Notification.objects.create(
                    recipient=session.student,
                    sender=request.user,
                    notification_type='session_created',
                    message=f'{request.user.get_full_name()} created a session with you.'
                )
            except Exception:
                pass
            messages.success(request, 'Session created.')
            return redirect('dashboard:mf_sessions')
        return render(request, self.template_name, {'form': form})


class MFOnboardingView(LoginRequiredMixin, MentorFacilitatorRequiredMixin, TemplateView):
    """Mentor Facilitator: onboarding and training resources for mentors"""
    template_name = 'dashboard/mf_onboarding.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any resources or guidance
        context['resources'] = [
            {'title': 'Mentor Guidelines', 'url': '/core/mentor-guidelines/', 'description': 'Official mentor guidelines and code of conduct'},
            {'title': 'Session Best Practices', 'url': '#', 'description': 'How to conduct effective mentorship sessions'},
            {'title': 'Platform Tutorial', 'url': '#', 'description': 'Video walkthrough of platform features'},
            {'title': 'Safety & Compliance', 'url': '#', 'description': 'Safety protocols and compliance requirements'},
            {'title': 'Communication Templates', 'url': '#', 'description': 'Email and message templates for mentors'},
        ]
        return context


class MFBackupView(LoginRequiredMixin, MentorFacilitatorRequiredMixin, TemplateView):
    """Mentor Facilitator: act as backup for assigned mentors"""
    template_name = 'dashboard/mf_backup.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from mentorship.models import MentorFacilitatorAssignment
        from accounts.models import User
        try:
            facilitator = self.request.user.mentor_facilitator_profile
            assignments = MentorFacilitatorAssignment.objects.filter(
                facilitator=facilitator
            ).exclude(mentor__isnull=True).select_related('mentor')
            mentors = [a.mentor for a in assignments if a.mentor]
            context['mentors'] = mentors
        except Exception:
            context['mentors'] = []
        return context


@login_required
def mf_approve_request(request, pk):
    """Mentor Facilitator: approve a mentorship request for an assigned mentor"""
    if not request.user.is_mentor_facilitator:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    from mentorship.models import MentorshipRequest, MentorFacilitatorAssignment
    mentorship = get_object_or_404(MentorshipRequest, pk=pk, status='pending')
    # Verify the mentor is assigned to this facilitator
    try:
        facilitator = request.user.mentor_facilitator_profile
        if not MentorFacilitatorAssignment.objects.filter(
            facilitator=facilitator, mentor=mentorship.mentor
        ).exists():
            messages.error(request, 'This mentor is not assigned to you.')
            return redirect('dashboard:mentor_facilitator_dashboard')
    except Exception:
        messages.error(request, 'Facilitator profile not found.')
        return redirect('dashboard:mentor_facilitator_dashboard')
    response_text = request.POST.get('response', '')
    mentorship.approve(response_text)
    ActivityLog.objects.create(
        user=request.user,
        action='mentor_facilitator_action',
        description=f'Approved request #{pk} for mentor {mentorship.mentor.get_full_name()}'
    )
    messages.success(request, f'Request approved for {mentorship.mentor.get_full_name()}!')
    return redirect('dashboard:mentor_facilitator_dashboard')


@login_required
def mf_reject_request(request, pk):
    """Mentor Facilitator: reject a mentorship request for an assigned mentor"""
    if not request.user.is_mentor_facilitator:
        messages.error(request, 'Access denied.')
        return redirect('dashboard:home')
    from mentorship.models import MentorshipRequest, MentorFacilitatorAssignment
    mentorship = get_object_or_404(MentorshipRequest, pk=pk, status='pending')
    try:
        facilitator = request.user.mentor_facilitator_profile
        if not MentorFacilitatorAssignment.objects.filter(
            facilitator=facilitator, mentor=mentorship.mentor
        ).exists():
            messages.error(request, 'This mentor is not assigned to you.')
            return redirect('dashboard:mentor_facilitator_dashboard')
    except Exception:
        messages.error(request, 'Facilitator profile not found.')
        return redirect('dashboard:mentor_facilitator_dashboard')
    response_text = request.POST.get('response', '')
    mentorship.reject(response_text)
    ActivityLog.objects.create(
        user=request.user,
        action='mentor_facilitator_action',
        description=f'Rejected request #{pk} for mentor {mentorship.mentor.get_full_name()}'
    )
    messages.info(request, f'Request for {mentorship.mentor.get_full_name()} declined.')
    return redirect('dashboard:mentor_facilitator_dashboard')


# ==================== FINANCE OFFICER: PAYMENTS LIST, REPORTS, EXPORT ====================

class FinancePaymentsView(LoginRequiredMixin, FinanceOfficerRequiredMixin, ListView):
    """Finance Officer: payment queue with filter/search"""
    template_name = 'dashboard/finance_payments.html'
    context_object_name = 'applications'
    paginate_by = 20

    def get_queryset(self):
        from applications.models import Application
        qs = Application.objects.exclude(status='draft').select_related(
            'applicant', 'mentorship_request__mentor', 'mentorship_request__student'
        ).order_by('-submitted_at')
        status = self.request.GET.get('status', '')
        if status:
            qs = qs.filter(status=status)
        search = self.request.GET.get('search', '')
        if search:
            qs = qs.filter(
                Q(tracking_code__icontains=search) |
                Q(email__icontains=search) |
                Q(applicant__email__icontains=search) |
                Q(mentorship_request__mentor__email__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from applications.models import Application, Payment
        context['pending_count'] = Application.objects.filter(status='pending_finance').count()
        context['approved_count'] = Payment.objects.filter(verified=True).count()
        context['rejected_count'] = Application.objects.filter(status='finance_rejected').count()
        return context


class FinanceSubscriptionPaymentsView(LoginRequiredMixin, FinanceOfficerRequiredMixin, ListView):
    """Finance Officer: subscription payment proofs for review"""
    template_name = 'dashboard/finance_subscription_payments.html'
    context_object_name = 'payment_proofs'
    paginate_by = 20

    def get_queryset(self):
        from payments.models import PaymentProof
        qs = PaymentProof.objects.filter(payment_type='subscription').select_related('user', 'reviewed_by').order_by('-submitted_at')
        status = self.request.GET.get('status', '')
        if status:
            qs = qs.filter(status=status)
        search = self.request.GET.get('search', '')
        if search:
            qs = qs.filter(
                Q(user__email__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from payments.models import PaymentProof
        context['pending_count'] = PaymentProof.objects.filter(status='pending', payment_type='subscription').count()
        context['approved_count'] = PaymentProof.objects.filter(status='approved', payment_type='subscription').count()
        context['rejected_count'] = PaymentProof.objects.filter(status='rejected', payment_type='subscription').count()
        return context


@login_required
def upload_payment_proof(request):
    """
    Handle payment proof upload for subscription (outside wizard).
    Creates a PaymentProof with pending status.
    """
    from payments.forms import PaymentProofForm
    from payments.models import PaymentProof
    from django.contrib import messages

    if request.method == 'POST':
        form = PaymentProofForm(request.POST, request.FILES)
        if form.is_valid():
            payment_proof = PaymentProof.objects.create(
                user=request.user,
                payment_type=form.cleaned_data['payment_type'],
                amount=float(form.cleaned_data['amount']),
                proof_image=form.cleaned_data['proof_image'],
                status='pending',
            )
            messages.success(request, 'Payment proof uploaded successfully. It will be reviewed by finance officer.')
            # Redirect to appropriate page (e.g., subscription wizard step 3 or dashboard)
            return redirect('dashboard:subscription_wizard_step', step=3)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PaymentProofForm(initial={
            'payment_type': 'subscription',
            'amount': 0,
        })

    return render(request, 'dashboard/upload_payment_proof.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_finance_officer)
def finance_subscription_payment_review(request, pk):
    """
    Finance officer reviews a subscription payment proof.
    Approve or reject a PaymentProof.
    """
    from payments.models import PaymentProof
    from django.contrib import messages
    from django.utils import timezone
    from core.models import ActivityLog

    payment_proof = get_object_or_404(PaymentProof, pk=pk, payment_type='subscription')

    if request.method == 'POST':
        action = request.POST.get('action')  # 'approve' or 'reject'
        if action == 'approve':
            payment_proof.status = 'approved'
            payment_proof.reviewed_by = request.user
            payment_proof.reviewed_at = timezone.now()
            payment_proof.save()
            # Update linked subscription if exists
            from payments.models import Subscription
            subscription = Subscription.objects.filter(payment_proof=payment_proof).first()
            if subscription:
                subscription.status = 'active'
                subscription.save()
            ActivityLog.objects.create(
                user=request.user,
                action='finance_officer_action',
                description=f'Approved subscription payment proof #{payment_proof.id} for {payment_proof.user.email}'
            )
            messages.success(request, f'Payment proof approved for {payment_proof.user.get_full_name()}.')
        elif action == 'reject':
            payment_proof.status = 'rejected'
            payment_proof.reviewed_by = request.user
            payment_proof.reviewed_at = timezone.now()
            payment_proof.save()
            ActivityLog.objects.create(
                user=request.user,
                action='finance_officer_action',
                description=f'Rejected subscription payment proof #{payment_proof.id} for {payment_proof.user.email}'
            )
            messages.warning(request, f'Payment proof rejected for {payment_proof.user.get_full_name()}.')
        else:
            messages.error(request, 'Invalid action.')
        return redirect('dashboard:finance_subscription_payments')

    return render(request, 'dashboard/finance_subscription_payment_review.html', {
        'payment_proof': payment_proof,
    })


class FinanceReportsView(LoginRequiredMixin, FinanceOfficerRequiredMixin, TemplateView):
    """Finance Officer: revenue charts and summary"""
    template_name = 'dashboard/finance_reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from applications.models import Payment
        from payments.models import PaymentProof, Subscription
        from django.db.models import Sum, Count
        from django.db.models.functions import TruncMonth
        import json

        # Application payment revenue
        total_revenue = Payment.objects.filter(verified=True).aggregate(
            total=Sum('amount')
        )['total'] or 0
        context['total_revenue'] = total_revenue
        context['verified_payments_count'] = Payment.objects.filter(verified=True).count()

        # Subscription revenue
        subscription_revenue = PaymentProof.objects.filter(
            status='approved', payment_type='subscription'
        ).aggregate(total=Sum('amount'))['total'] or 0
        context['subscription_revenue'] = subscription_revenue
        context['active_subscriptions_count'] = Subscription.objects.filter(status='active').count()
        context['pending_subscription_payments_count'] = PaymentProof.objects.filter(
            status='pending', payment_type='subscription'
        ).count()

        # Combined revenue
        context['combined_revenue'] = total_revenue + subscription_revenue

        # Revenue by month for chart (application payments)
        monthly = Payment.objects.filter(verified=True).annotate(
            month=TruncMonth('verified_at')
        ).values('month').annotate(total=Sum('amount')).order_by('month')[:12]
        context['revenue_monthly_labels'] = json.dumps([m['month'].strftime('%b %Y') for m in monthly])
        context['revenue_monthly_data'] = json.dumps([float(m['total']) for m in monthly])

        # Subscription revenue by month
        subscription_monthly = PaymentProof.objects.filter(
            status='approved', payment_type='subscription'
        ).annotate(
            month=TruncMonth('reviewed_at')
        ).values('month').annotate(total=Sum('amount')).order_by('month')[:12]
        context['subscription_monthly_labels'] = json.dumps([m['month'].strftime('%b %Y') for m in subscription_monthly])
        context['subscription_monthly_data'] = json.dumps([float(m['total']) for m in subscription_monthly])

        return context


class FinancePaymentSettingsView(LoginRequiredMixin, FinanceOfficerRequiredMixin, UpdateView):
    """Finance Officer: update subscription and application fees"""
    model = PaymentSettings
    fields = ['student_payment_amount', 'application_fee', 'subscription_fee',
              'payment_number', 'payment_code', 'payment_instructions',
              'bank_name', 'account_number', 'account_name', 'mobile_money_number']
    template_name = 'dashboard/finance_payment_settings.html'
    success_url = reverse_lazy('dashboard:finance_dashboard')

    def get_object(self, queryset=None):
        # Get the latest PaymentSettings or create a default one
        obj = PaymentSettings.objects.order_by('-updated_at').first()
        if not obj:
            obj = PaymentSettings.objects.create(
                student_payment_amount=0,
                application_fee=0,
                subscription_fee=0
            )
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from applications.models import Payment
        from django.db.models import Sum
        from django.db.models.functions import TruncMonth, TruncDate

        total_revenue = Payment.objects.filter(verified=True).aggregate(
            total=Sum('amount')
        )['total'] or 0
        context['total_revenue'] = total_revenue
        context['verified_payments_count'] = Payment.objects.filter(verified=True).count()

        # Revenue by month for chart
        monthly = Payment.objects.filter(verified=True).annotate(
            month=TruncMonth('verified_at')
        ).values('month').annotate(total=Sum('amount')).order_by('month')[:12]
        context['revenue_monthly_labels'] = json.dumps([m['month'].strftime('%b %Y') for m in monthly])
        context['revenue_monthly_data'] = json.dumps([float(m['total']) for m in monthly])
        return context


@login_required
@user_passes_test(lambda u: u.is_finance_officer)
def finance_export(request):
    """Finance Officer: export payments as CSV or PDF"""
    import csv
    from django.http import HttpResponse
    from applications.models import Payment

    format_type = request.GET.get('format', 'csv')
    status = request.GET.get('status', '')  # verified, pending, all

    qs = Payment.objects.select_related('application', 'application__applicant', 'verified_by').order_by('-submitted_at')
    if status == 'verified':
        qs = qs.filter(verified=True)
    elif status == 'pending':
        qs = qs.filter(verified=False)

    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="finance_payments_{timezone.now().strftime("%Y%m%d")}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Transaction Code', 'Amount', 'Status', 'Student', 'Application', 'Submitted', 'Verified At'])
        for p in qs:
            writer.writerow([
                p.transaction_code,
                p.amount,
                'Verified' if p.verified else 'Pending',
                p.application.applicant.get_full_name() if p.application.applicant else p.application.email,
                p.application.tracking_code,
                p.submitted_at.strftime('%Y-%m-%d %H:%M'),
                p.verified_at.strftime('%Y-%m-%d %H:%M') if p.verified_at else '',
            ])
        return response

    return redirect('dashboard:finance_reports')


# ==================== MENTORSHIP APPLICATIONS MANAGEMENT ====================

class AdminApplicationListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """Admin view to list all mentorship applications"""
    template_name = 'dashboard/admin_applications.html'
    context_object_name = 'applications'
    paginate_by = 20

    def get_queryset(self):
        from applications.models import Application
        queryset = Application.objects.exclude(status='draft').select_related(
            'applicant', 'selected_mentor', 'selected_availability_slot'
        ).order_by('-submitted_at')

        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(tracking_code__icontains=search) |
                Q(school__icontains=search) |
                Q(selected_mentor__email__icontains=search)
            )

        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)

        mentor_id = self.request.GET.get('mentor', '')
        if mentor_id:
            queryset = queryset.filter(selected_mentor_id=mentor_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from applications.models import Application
        qs = Application.objects.exclude(status='draft')
        context['total_applications'] = qs.count()
        context['pending_count'] = qs.filter(status='pending_review').count()
        context['approved_count'] = qs.filter(status__in=['approved', 'enrolled']).count()
        context['rejected_count'] = qs.filter(status__in=['finance_rejected', 'review_rejected']).count()
        return context


class AdminApplicationDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """Admin view to see mentorship application details"""
    template_name = 'dashboard/admin_application_detail.html'
    context_object_name = 'application'

    def get_object(self):
        from applications.models import Application
        return get_object_or_404(Application, pk=self.kwargs['pk'])

    def get_queryset(self):
        from applications.models import Application
        return Application.objects.select_related(
            'applicant', 'selected_mentor', 'selected_availability_slot'
        )


@login_required
@user_passes_test(lambda u: u.is_admin_user)
def admin_application_approve(request, pk):
    """Admin/Mentorship Department approve application"""
    from applications.models import Application
    from applications.models import ActivityLog as AppActivityLog
    from django.contrib.contenttypes.models import ContentType

    application = get_object_or_404(Application, pk=pk, status='pending_review')
    application.status = 'approved'
    application.save(update_fields=['status'])

    ct = ContentType.objects.get_for_model(Application)
    AppActivityLog.objects.create(
        content_type=ct,
        object_id=application.id,
        action_type='status_change',
        previous_status='pending_review',
        new_status='approved',
        details='Application approved by admin.',
        performed_by=request.user,
    )
    ActivityLog.objects.create(
        user=request.user,
        action='admin_action',
        description=f'Approved mentorship application {application.tracking_code} ({application.email})'
    )
    try:
        from notifications.models import Notification
        if application.applicant:
            Notification.objects.create(
                recipient=application.applicant,
                sender=request.user,
                notification_type='request_approved',
                title='Application approved',
                message=f'Your mentorship application {application.tracking_code} has been approved.'
            )
    except Exception:
        pass
    messages.success(request, f'Application {application.tracking_code} approved.')
    return redirect('dashboard:admin_applications')


@login_required
@user_passes_test(lambda u: u.is_admin_user)
def admin_application_reject(request, pk):
    """Admin/Mentorship Department reject application"""
    from applications.models import Application
    from applications.models import ActivityLog as AppActivityLog
    from django.contrib.contenttypes.models import ContentType

    application = get_object_or_404(Application, pk=pk, status='pending_review')
    reason = request.POST.get('feedback', request.POST.get('reason', 'Application rejected.'))
    application.status = 'review_rejected'
    application.save(update_fields=['status'])

    ct = ContentType.objects.get_for_model(Application)
    AppActivityLog.objects.create(
        content_type=ct,
        object_id=application.id,
        action_type='status_change',
        previous_status='pending_review',
        new_status='review_rejected',
        details=reason,
        performed_by=request.user,
    )
    ActivityLog.objects.create(
        user=request.user,
        action='admin_action',
        description=f'Rejected mentorship application {application.tracking_code} ({application.email})'
    )
    try:
        from notifications.models import Notification
        if application.applicant:
            Notification.objects.create(
                recipient=application.applicant,
                sender=request.user,
                notification_type='request_rejected',
                title='Application rejected',
                message=f'Your mentorship application {application.tracking_code} was rejected. Reason: {reason}'
            )
    except Exception:
        pass
    messages.info(request, 'Application rejected.')
    return redirect('dashboard:admin_applications')


# ==================== SESSION MANAGEMENT ====================

class AdminSessionListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """Admin view to list all sessions"""
    template_name = 'dashboard/admin_sessions.html'
    context_object_name = 'sessions'
    paginate_by = 20

    def get_queryset(self):
        from sessions_app.models import Session
        queryset = Session.objects.select_related('mentor', 'student').order_by('-start')

        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(mentor__email__icontains=search) |
                Q(student__email__icontains=search) |
                Q(title__icontains=search)
            )

        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)

        session_type = self.request.GET.get('type', '')
        if session_type:
            queryset = queryset.filter(session_type=session_type)

        mentor_id = self.request.GET.get('mentor', '')
        if mentor_id:
            queryset = queryset.filter(mentor_id=mentor_id)

        student_id = self.request.GET.get('student', '')
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        date_from = self.request.GET.get('date_from', '')
        if date_from:
            queryset = queryset.filter(start__date__gte=date_from)

        date_to = self.request.GET.get('date_to', '')
        if date_to:
            queryset = queryset.filter(start__date__lte=date_to)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from sessions_app.models import Session
        from accounts.models import User
        context['total_sessions'] = Session.objects.count()
        context['scheduled_count'] = Session.objects.filter(status='scheduled').count()
        context['completed_count'] = Session.objects.filter(status='completed').count()
        context['cancelled_count'] = Session.objects.filter(status='cancelled').count()
        context['mentors_for_filter'] = User.objects.filter(role='mentor').order_by('first_name')
        context['students_for_filter'] = User.objects.filter(role='student').order_by('first_name')
        return context


# ==================== POST MANAGEMENT ====================

class AdminPostListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """Admin view to list all feed posts"""
    template_name = 'dashboard/admin_posts.html'
    context_object_name = 'posts'
    paginate_by = 20

    def get_queryset(self):
        from feed.models import Post
        queryset = Post.objects.select_related('author').order_by('-created_at')

        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(author__email__icontains=search) |
                Q(content__icontains=search)
            )

        status = self.request.GET.get('status', '')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status == 'pinned':
            queryset = queryset.filter(is_pinned=True)
        elif status == 'approved':
            queryset = queryset.filter(is_approved=True)
        elif status == 'unapproved':
            queryset = queryset.filter(is_approved=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from feed.models import Post, Comment, Like
        context['total_posts'] = Post.objects.count()
        context['active_posts'] = Post.objects.filter(is_active=True).count()
        context['pinned_posts'] = Post.objects.filter(is_pinned=True).count()
        context['total_comments'] = Comment.objects.count()
        context['total_likes'] = Like.objects.count()
        return context


@login_required
@user_passes_test(lambda u: u.is_admin_user)
def toggle_post_status(request, pk):
    """Toggle post active status"""
    from feed.models import Post
    post = get_object_or_404(Post, pk=pk)
    post.is_active = not post.is_active
    post.save()

    ActivityLog.objects.create(
        user=request.user,
        action='admin_action',
        description=f'{"Activated" if post.is_active else "Deactivated"} post #{post.id}'
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'is_active': post.is_active})
    messages.success(request, f'Post has been {"activated" if post.is_active else "deactivated"}.')
    return redirect('dashboard:admin_posts')


@login_required
@user_passes_test(lambda u: u.is_admin_user)
def toggle_post_pinned(request, pk):
    """Toggle post pinned status"""
    from feed.models import Post
    post = get_object_or_404(Post, pk=pk)
    post.is_pinned = not post.is_pinned
    post.save()

    ActivityLog.objects.create(
        user=request.user,
        action='admin_action',
        description=f'{"Pinned" if post.is_pinned else "Unpinned"} post #{post.id}'
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'is_pinned': post.is_pinned})
    messages.success(request, f'Post has been {"pinned" if post.is_pinned else "unpinned"}.')
    return redirect('dashboard:admin_posts')


@login_required
@user_passes_test(lambda u: u.is_admin_user)
def approve_post(request, pk):
    """Approve a post (make it visible in feed)"""
    from feed.models import Post
    from django.utils import timezone
    post = get_object_or_404(Post, pk=pk)
    if not post.is_approved:
        post.is_approved = True
        post.approved_at = timezone.now()
        post.approved_by = request.user
        post.save()

        ActivityLog.objects.create(
            user=request.user,
            action='admin_action',
            description=f'Approved post #{post.id}'
        )
        messages.success(request, 'Post has been approved.')
    else:
        messages.info(request, 'Post is already approved.')
    return redirect('dashboard:admin_posts')


@login_required
@user_passes_test(lambda u: u.is_admin_user)
def delete_post(request, pk):
    """Delete a post"""
    from feed.models import Post
    post = get_object_or_404(Post, pk=pk)
    post_id = post.id
    post.delete()

    ActivityLog.objects.create(
        user=request.user,
        action='admin_action',
        description=f'Deleted post #{post_id}'
    )
    messages.success(request, 'Post has been deleted.')
    return redirect('dashboard:admin_posts')


# ==================== REVIEW MANAGEMENT ====================

class AdminReviewListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """Admin view to list all reviews"""
    template_name = 'dashboard/admin_reviews.html'
    context_object_name = 'reviews'
    paginate_by = 20

    def get_queryset(self):
        from mentorship.models import Review
        queryset = Review.objects.select_related('student', 'mentor').order_by('-created_at')

        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(student__email__icontains=search) |
                Q(mentor__email__icontains=search) |
                Q(content__icontains=search)
            )

        rating = self.request.GET.get('rating', '')
        if rating:
            queryset = queryset.filter(rating=rating)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from mentorship.models import Review
        context['total_reviews'] = Review.objects.count()
        avg = Review.objects.aggregate(avg=Avg('rating'))['avg']
        context['average_rating'] = round(avg, 2) if avg else 0
        context['five_star'] = Review.objects.filter(rating=5).count()
        context['four_star'] = Review.objects.filter(rating=4).count()
        context['three_star'] = Review.objects.filter(rating=3).count()
        context['two_star'] = Review.objects.filter(rating=2).count()
        context['one_star'] = Review.objects.filter(rating=1).count()
        return context


@login_required
@user_passes_test(lambda u: u.is_admin_user)
def delete_review(request, pk):
    """Delete a review"""
    from mentorship.models import Review
    review = get_object_or_404(Review, pk=pk)
    mentor = review.mentor
    review.delete()

    # Update mentor's rating
    try:
        mentor.mentor_profile.update_rating()
    except Exception:
        pass

    ActivityLog.objects.create(
        user=request.user,
        action='admin_action',
        description=f'Deleted review for {mentor.email}'
    )
    messages.success(request, 'Review has been deleted.')
    return redirect('dashboard:admin_reviews')


# ==================== NOTIFICATION MANAGEMENT ====================

class AdminNotificationListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """Admin view to list all notifications"""
    template_name = 'dashboard/admin_notifications.html'
    context_object_name = 'notifications'
    paginate_by = 30

    def get_queryset(self):
        from notifications.models import Notification
        queryset = Notification.objects.select_related('recipient', 'sender').order_by('-created_at')

        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(recipient__email__icontains=search) |
                Q(message__icontains=search)
            )

        notif_type = self.request.GET.get('type', '')
        if notif_type:
            queryset = queryset.filter(notification_type=notif_type)

        status = self.request.GET.get('status', '')
        if status == 'read':
            queryset = queryset.filter(is_read=True)
        elif status == 'unread':
            queryset = queryset.filter(is_read=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from notifications.models import Notification
        context['total_notifications'] = Notification.objects.count()
        context['unread_count'] = Notification.objects.filter(is_read=False).count()
        context['system_count'] = Notification.objects.filter(notification_type='system').count()
        return context


# ==================== REPORTS & ANALYTICS ====================

class AdminReportsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Admin view for reports and analytics"""
    template_name = 'dashboard/admin_reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        month_ago = now - timedelta(days=30)
        week_ago = now - timedelta(days=7)
        three_months_ago = now - timedelta(days=90)

        # User Statistics
        context['total_users'] = User.objects.count()
        context['new_users_week'] = User.objects.filter(date_joined__gte=week_ago).count()
        context['new_users_month'] = User.objects.filter(date_joined__gte=month_ago).count()

        # User growth data for chart (last 90 days by week)
        user_growth_weekly = User.objects.filter(
            date_joined__gte=three_months_ago
        ).annotate(
            week=TruncWeek('date_joined')
        ).values('week').annotate(
            count=Count('id')
        ).order_by('week')
        context['user_growth_weekly_labels'] = json.dumps([item['week'].strftime('%b %d') for item in user_growth_weekly])
        context['user_growth_weekly_data'] = json.dumps([item['count'] for item in user_growth_weekly])

        # Monthly user growth
        user_growth_monthly = User.objects.annotate(
            month=TruncMonth('date_joined')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('-month')[:12]
        user_growth_monthly = list(reversed(list(user_growth_monthly)))
        context['user_growth_monthly_labels'] = json.dumps([item['month'].strftime('%b %Y') for item in user_growth_monthly])
        context['user_growth_monthly_data'] = json.dumps([item['count'] for item in user_growth_monthly])

        # Mentorship Request Statistics
        try:
            from mentorship.models import MentorshipRequest, Review

            # Request growth over time
            request_growth = MentorshipRequest.objects.filter(
                created_at__gte=three_months_ago
            ).annotate(
                week=TruncWeek('created_at')
            ).values('week').annotate(
                count=Count('id')
            ).order_by('week')
            context['request_growth_labels'] = json.dumps([item['week'].strftime('%b %d') for item in request_growth])
            context['request_growth_data'] = json.dumps([item['count'] for item in request_growth])

            # Request completion rate
            total = MentorshipRequest.objects.count()
            completed = MentorshipRequest.objects.filter(status='completed').count()
            context['completion_rate'] = round((completed / total * 100), 1) if total > 0 else 0

            # Top performing mentors
            from profiles.models import MentorProfile
            context['top_mentors'] = MentorProfile.objects.filter(
                user__is_active=True
            ).select_related('user').order_by('-rating', '-total_reviews')[:10]

            # Rating distribution
            context['rating_distribution'] = json.dumps([
                Review.objects.filter(rating=5).count(),
                Review.objects.filter(rating=4).count(),
                Review.objects.filter(rating=3).count(),
                Review.objects.filter(rating=2).count(),
                Review.objects.filter(rating=1).count(),
            ])
        except Exception:
            context['request_growth_labels'] = json.dumps([])
            context['request_growth_data'] = json.dumps([])
            context['completion_rate'] = 0
            context['top_mentors'] = []
            context['rating_distribution'] = json.dumps([0, 0, 0, 0, 0])

        # Feed engagement
        try:
            from feed.models import Post, Comment, Like

            # Posts over time
            post_growth = Post.objects.filter(
                created_at__gte=three_months_ago
            ).annotate(
                week=TruncWeek('created_at')
            ).values('week').annotate(
                count=Count('id')
            ).order_by('week')
            context['post_growth_labels'] = json.dumps([item['week'].strftime('%b %d') for item in post_growth])
            context['post_growth_data'] = json.dumps([item['count'] for item in post_growth])

            # Engagement stats
            context['avg_likes_per_post'] = round(Like.objects.count() / max(Post.objects.count(), 1), 1)
            context['avg_comments_per_post'] = round(Comment.objects.count() / max(Post.objects.count(), 1), 1)
        except Exception:
            context['post_growth_labels'] = json.dumps([])
            context['post_growth_data'] = json.dumps([])
            context['avg_likes_per_post'] = 0
            context['avg_comments_per_post'] = 0

        # Activity summary
        context['activity_summary'] = ActivityLog.objects.values('action').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        return context


class AdminExportDataView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Export data as CSV/JSON"""

    def get(self, request):
        import csv
        from django.http import HttpResponse

        export_type = request.GET.get('type', 'users')
        format_type = request.GET.get('format', 'csv')

        if format_type == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{export_type}_{timezone.now().strftime("%Y%m%d")}.csv"'
            writer = csv.writer(response)

            if export_type == 'users':
                writer.writerow(['ID', 'Email', 'First Name', 'Last Name', 'Role', 'Active', 'Joined'])
                for user in User.objects.all():
                    writer.writerow([user.id, user.email, user.first_name, user.last_name, user.role, user.is_active, user.date_joined])

            elif export_type == 'mentors':
                from profiles.models import MentorProfile
                writer.writerow(['ID', 'Email', 'Name', 'Expertise', 'Rating', 'Reviews', 'Verified', 'Featured'])
                for mentor in MentorProfile.objects.select_related('user').all():
                    writer.writerow([mentor.id, mentor.user.email, mentor.user.get_full_name(), mentor.expertise, mentor.rating, mentor.total_reviews, mentor.is_verified, mentor.is_featured])

            elif export_type == 'requests':
                from mentorship.models import MentorshipRequest
                writer.writerow(['ID', 'Student', 'Mentor', 'Subject', 'Status', 'Created'])
                for req in MentorshipRequest.objects.select_related('student', 'mentor').all():
                    writer.writerow([req.id, req.student.email, req.mentor.email, req.subject, req.status, req.created_at])

            return response

        elif format_type == 'json':
            data = []

            if export_type == 'users':
                for user in User.objects.all():
                    data.append({
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'role': user.role,
                        'is_active': user.is_active,
                        'date_joined': user.date_joined.isoformat()
                    })

            return JsonResponse(data, safe=False)

        return JsonResponse({'error': 'Invalid format'}, status=400)


# ==================== SUBSCRIPTION WORKFLOW ====================

@login_required
def subscription_wizard(request, step=None):
    """
    Multi-step subscription purchase wizard for students.
    Steps: 1=Choose Plan, 2=Payment Details, 3=Review & Confirm, 4=Processing
    """
    if not request.user.is_student:
        messages.warning(request, 'Only students can subscribe.')
        return redirect('dashboard:student_dashboard')
    
    # Determine current step
    if step is None:
        step = 1
    else:
        step = int(step)
    
    # Ensure step is between 1 and 4
    step = max(1, min(4, step))
    
    # Get subscription fee from PaymentSettings
    from payments.models import PaymentSettings
    settings = PaymentSettings.objects.order_by('-updated_at').first()
    subscription_fee = settings.subscription_fee if settings else 0
    
    # Initialize session data if not present
    if 'subscription_wizard' not in request.session:
        request.session['subscription_wizard'] = {
            'plan': 'monthly',
            'payment_type': 'subscription',
            'amount': float(subscription_fee),
        }
    
    wizard_data = request.session['subscription_wizard']
    
    # Prepare base context
    context = {
        'step': step,
        'subscription_fee': subscription_fee,
        'progress_percent': int((step / 4) * 100),
    }
    
    # Handle POST requests
    if request.method == 'POST':
        if step == 1:
            plan = request.POST.get('plan', 'monthly')
            wizard_data['plan'] = plan
            request.session.modified = True
            return redirect('dashboard:subscription_wizard_step', step=2)
        
        elif step == 2:
            from payments.forms import PaymentProofForm
            form = PaymentProofForm(request.POST, request.FILES)
            if form.is_valid():
                # Create PaymentProof with pending status
                from payments.models import PaymentProof
                payment_proof = PaymentProof.objects.create(
                    user=request.user,
                    payment_type=form.cleaned_data['payment_type'],
                    amount=float(form.cleaned_data['amount']),
                    proof_image=form.cleaned_data['proof_image'],
                    status='pending',
                )
                # Store payment proof ID in session
                wizard_data['payment_proof_id'] = payment_proof.id
                wizard_data['payment_type'] = form.cleaned_data['payment_type']
                wizard_data['amount'] = float(form.cleaned_data['amount'])
                request.session.modified = True
                return redirect('dashboard:subscription_wizard_step', step=3)
            else:
                # Form invalid, re-render with errors
                context['form'] = form
        
        elif step == 3:
            # Create Subscription linked to the PaymentProof
            from payments.models import PaymentProof, Subscription
            from django.utils import timezone
            
            payment_proof_id = wizard_data.get('payment_proof_id')
            if not payment_proof_id:
                messages.error(request, 'Payment proof missing. Please start over.')
                return redirect('dashboard:subscription_wizard')
            
            payment_proof = PaymentProof.objects.get(id=payment_proof_id, user=request.user)
            
            # Determine end date based on plan
            start_date = timezone.now().date()
            end_date = None
            plan = wizard_data.get('plan', 'monthly')
            if plan == 'monthly':
                end_date = start_date + timezone.timedelta(days=30)
            elif plan == 'yearly':
                end_date = start_date + timezone.timedelta(days=365)
            # lifetime has no end date
            
            subscription = Subscription.objects.create(
                user=request.user,
                plan=plan,
                status='pending',
                start_date=start_date,
                end_date=end_date,
                payment_proof=payment_proof,
            )
            
            # Clear session data
            del request.session['subscription_wizard']
            request.session.modified = True
            
            # Notify finance officer (optional)
            # Redirect to processing step
            return redirect('dashboard:subscription_wizard_step', step=4)
        
        elif step == 4:
            # Processing step - just show success message
            pass
    
    # Fill step-specific context (if not already set by POST error)
    if step == 1:
        context['plans'] = [
            {'value': 'monthly', 'name': 'Monthly', 'price': subscription_fee},
            {'value': 'yearly', 'name': 'Yearly', 'price': subscription_fee * 12},
            {'value': 'lifetime', 'name': 'Lifetime', 'price': subscription_fee * 120},
        ]
        context['selected_plan'] = wizard_data.get('plan', 'monthly')
    
    elif step == 2:
        if 'form' not in context:
            from payments.forms import PaymentProofForm
            context['form'] = PaymentProofForm(initial={
                'payment_type': wizard_data.get('payment_type', 'subscription'),
                'amount': wizard_data.get('amount', subscription_fee),
            })
        # Pass payment info for display
        # Pass payment info for display
        context['payment_settings'] = settings
    
    elif step == 3:
        from payments.models import Subscription
        context['wizard_data'] = wizard_data
        context['plan_display'] = dict(Subscription.PLAN_CHOICES).get(wizard_data.get('plan', 'monthly'), 'Monthly')
    
    elif step == 4:
        # Show success message
        pass
    
    return render(request, 'dashboard/subscription_wizard_step.html', context)


@login_required
def download_subscription_receipt(request):
    """Generate an HTML printable receipt for the student's active subscription."""
    from payments.models import Subscription, PaymentProof
    from django.utils import timezone

    subscription = Subscription.objects.filter(
        user=request.user, status='active'
    ).select_related('payment_proof').first()

    if not subscription:
        messages.warning(request, 'You do not have an active subscription.')
        return redirect('dashboard:student_dashboard')

    context = {
        'subscription': subscription,
        'user': request.user,
        'generated_at': timezone.now(),
    }
    return render(request, 'dashboard/subscription_receipt.html', context)

