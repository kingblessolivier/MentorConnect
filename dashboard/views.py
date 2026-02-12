"""
Dashboard App Views
Role-based dashboards for Students, Mentors, and Admins
"""

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

from accounts.models import User
from core.models import SiteSettings, ThemeSettings, ActivityLog


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


class DashboardRedirectView(LoginRequiredMixin, View):
    """Redirects user to their role-specific dashboard"""
    def get(self, request):
        if request.user.is_admin_user:
            return redirect('dashboard:admin_dashboard')
        elif request.user.is_mentor:
            return redirect('dashboard:mentor_dashboard')
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
            context['approved_sessions'] = MentorshipRequest.objects.filter(
                student=user, status='approved'
            ).select_related('mentor')[:5]
        except Exception:
            context['pending_requests'] = []
            context['approved_sessions'] = []

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
            from applications.models import GuestApplication
            linked = GuestApplication.objects.filter(student=user, status='approved').order_by('-approved_at')[:3]
            context['linked_applications_with_feedback'] = [a for a in linked if a.mentor_feedback]
        except Exception:
            context['linked_applications_with_feedback'] = []

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
            from applications.models import GuestApplication
            context['pending_requests'] = MentorshipRequest.objects.filter(
                mentor=user, status='pending'
            ).select_related('student')[:10]
            context['total_pending'] = MentorshipRequest.objects.filter(
                mentor=user, status='pending'
            ).count()
            context['guest_applications_pending'] = GuestApplication.objects.filter(
                mentor=user, status='pending'
            ).order_by('-created_at')[:5]
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
    fields = [
        'site_name', 'site_tagline', 'site_logo', 'site_favicon',
        'contact_email', 'contact_phone', 'contact_address',
        'facebook_url', 'twitter_url', 'linkedin_url', 'instagram_url',
        'footer_text', 'enable_chat', 'enable_feed', 'enable_notifications',
        'enable_text_to_speech', 'maintenance_mode', 'maintenance_message'
    ]
    success_url = reverse_lazy('dashboard:admin_settings')

    def get_object(self):
        return SiteSettings.get_settings()

    def form_valid(self, form):
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

        from mentorship.models import MentorshipRequest, Review
        context['total_requests'] = MentorshipRequest.objects.filter(mentor=mentor.user).count()
        context['pending_requests'] = MentorshipRequest.objects.filter(mentor=mentor.user, status='pending').count()
        context['completed_requests'] = MentorshipRequest.objects.filter(mentor=mentor.user, status='completed').count()
        context['recent_requests'] = MentorshipRequest.objects.filter(mentor=mentor.user).select_related('student')[:10]
        context['reviews'] = Review.objects.filter(mentor=mentor.user).select_related('student')[:10]

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


# ==================== GUEST APPLICATIONS MANAGEMENT ====================

class AdminApplicationListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """Admin view to list all guest applications"""
    template_name = 'dashboard/admin_applications.html'
    context_object_name = 'applications'
    paginate_by = 20

    def get_queryset(self):
        from applications.models import GuestApplication
        queryset = GuestApplication.objects.select_related('mentor', 'student').order_by('-created_at')

        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(school__icontains=search) |
                Q(mentor__email__icontains=search)
            )

        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)

        mentor_id = self.request.GET.get('mentor', '')
        if mentor_id:
            queryset = queryset.filter(mentor_id=mentor_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from applications.models import GuestApplication
        context['total_applications'] = GuestApplication.objects.count()
        context['pending_count'] = GuestApplication.objects.filter(status='pending').count()
        context['approved_count'] = GuestApplication.objects.filter(status='approved').count()
        context['rejected_count'] = GuestApplication.objects.filter(status='rejected').count()
        return context


class AdminApplicationDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """Admin view to see application details"""
    template_name = 'dashboard/admin_application_detail.html'
    context_object_name = 'application'

    def get_object(self):
        from applications.models import GuestApplication
        return get_object_or_404(GuestApplication, pk=self.kwargs['pk'])


@login_required
@user_passes_test(lambda u: u.is_admin_user)
def admin_application_approve(request, pk):
    """Admin approve application"""
    from applications.models import GuestApplication
    from applications.services import send_approval_email
    application = get_object_or_404(GuestApplication, pk=pk)
    feedback = request.POST.get('feedback', '')
    application.approve(feedback=feedback)
    send_approval_email(application)
    ActivityLog.objects.create(
        user=request.user,
        action='admin_action',
        description=f'Approved guest application #{pk} ({application.email})'
    )
    messages.success(request, f'Application approved. Invitation sent to {application.email}.')
    return redirect('dashboard:admin_applications')


@login_required
@user_passes_test(lambda u: u.is_admin_user)
def admin_application_reject(request, pk):
    """Admin reject application"""
    from applications.models import GuestApplication
    application = get_object_or_404(GuestApplication, pk=pk)
    feedback = request.POST.get('feedback', '')
    application.reject(feedback=feedback)
    ActivityLog.objects.create(
        user=request.user,
        action='admin_action',
        description=f'Rejected guest application #{pk} ({application.email})'
    )
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
        queryset = Session.objects.select_related('mentor', 'student').order_by('-scheduled_time')

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
            queryset = queryset.filter(scheduled_time__date__gte=date_from)

        date_to = self.request.GET.get('date_to', '')
        if date_to:
            queryset = queryset.filter(scheduled_time__date__lte=date_to)

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

