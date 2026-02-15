from django.views import View
from django.http import HttpResponse

# Simple views for mentor/mentee application
class ApplyAsMentorView(View):
    def get(self, request):
        return render(request, 'profiles/apply_as_mentor.html')

class ApplyForMentorshipView(View):
    def get(self, request):
        return render(request, 'profiles/apply_for_mentorship.html')
"""
Profiles App Views
Profile viewing and editing for students and mentors
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import DetailView, UpdateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.conf import settings

from accounts.models import User
from .models import StudentProfile, MentorProfile, Follow


class ProfileDetailView(LoginRequiredMixin, DetailView):
    """
    View any user's profile - redirects to appropriate profile type
    """
    model = User
    template_name = 'profiles/detail.html'
    context_object_name = 'profile_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object

        # Check if current user follows this user
        context['is_following'] = Follow.objects.filter(
            follower=self.request.user,
            followed=user
        ).exists()

        # Get follower/following counts
        context['followers_count'] = user.followers.count()
        context['following_count'] = user.following.count()

        return context


class MentorProfileView(DetailView):
    """
    Public mentor profile view with comprehensive details
    """
    model = MentorProfile
    template_name = 'profiles/mentor_detail.html'
    context_object_name = 'profile'

    def get_object(self):
        return get_object_or_404(MentorProfile, user_id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mentor_profile = self.object
        mentor_user = self.object.user

        # Check if current user follows this mentor
        if self.request.user.is_authenticated:
            context['is_following'] = Follow.objects.filter(
                follower=self.request.user,
                followed=mentor_user
            ).exists()
        else:
            context['is_following'] = False

        # Get follower count
        context['followers_count'] = mentor_user.followers.count()

        # Get mentor's availability
        try:
            from sessions_app.models import Availability
            context['availabilities'] = Availability.objects.filter(
                mentor=mentor_user,
                is_active=True
            ).order_by('day_of_week')
        except Exception:
            context['availabilities'] = []

        # Get mentorship statistics
        try:
            from mentorship.models import MentorshipRequest, Review

            # Count statistics
            context['total_requests'] = MentorshipRequest.objects.filter(
                mentor=mentor_user
            ).count()
            context['completed_mentorships'] = MentorshipRequest.objects.filter(
                mentor=mentor_user,
                status='completed'
            ).count()
            context['active_mentees'] = MentorshipRequest.objects.filter(
                mentor=mentor_user,
                status__in=['approved', 'in_progress']
            ).count()

            # Get recent reviews
            context['recent_reviews'] = Review.objects.filter(
                mentor=mentor_user
            ).select_related('student').order_by('-created_at')[:5]
            context['total_reviews'] = Review.objects.filter(
                mentor=mentor_user
            ).count()
        except Exception:
            context['total_requests'] = 0
            context['completed_mentorships'] = 0
            context['active_mentees'] = 0
            context['recent_reviews'] = []
            context['total_reviews'] = 0

        # Get mentor's posts
        try:
            from feed.models import Post
            context['mentor_posts'] = Post.objects.filter(
                author=mentor_user,
                is_published=True
            ).order_by('-created_at')[:5]
        except Exception:
            context['mentor_posts'] = []

        # Check if user can request mentorship
        if self.request.user.is_authenticated and self.request.user.is_student:
            try:
                from mentorship.models import MentorshipRequest
                pending_request = MentorshipRequest.objects.filter(
                    student=self.request.user,
                    mentor=mentor_user,
                    status='pending'
                ).exists()
                approved_request = MentorshipRequest.objects.filter(
                    student=self.request.user,
                    mentor=mentor_user,
                    status='approved'
                ).exists()
                context['has_pending_request'] = pending_request
                context['has_approved_request'] = approved_request
            except Exception:
                context['has_pending_request'] = False
                context['has_approved_request'] = False

        return context


class StudentProfileView(LoginRequiredMixin, DetailView):
    """
    Student profile view (only visible to logged in users)
    """
    model = StudentProfile
    template_name = 'profiles/student_detail.html'
    context_object_name = 'profile'

    def get_object(self):
        return get_object_or_404(StudentProfile, user_id=self.kwargs['pk'])


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """
    Generic profile edit - redirects to appropriate edit view
    """
    def get(self, request, *args, **kwargs):
        if request.user.is_student:
            return redirect('profiles:student_edit')
        elif request.user.is_mentor:
            return redirect('profiles:mentor_edit')
        return redirect('dashboard:home')


class StudentProfileEditView(LoginRequiredMixin, UpdateView):
    """
    Edit student profile - now supports section-based editing
    """
    model = StudentProfile
    template_name = 'profiles/student_edit.html'
    fields = [
        'bio', 'headline', 'institution', 'field_of_study',
        'graduation_year', 'skills', 'interests', 'goals',
        'cv', 'linkedin_url', 'github_url', 'portfolio_url'
    ]
    success_url = reverse_lazy('profiles:student_edit')

    def get_object(self):
        profile, created = StudentProfile.objects.get_or_create(
            user=self.request.user
        )
        return profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_object()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        section = request.POST.get('section', 'all')

        # Handle based on section
        if section == 'photo':
            avatar = request.FILES.get('avatar')
            if avatar:
                request.user.avatar = avatar
                request.user.save()
                messages.success(request, 'Profile photo updated!')

        elif section == 'basic':
            request.user.first_name = request.POST.get('first_name', request.user.first_name)
            request.user.last_name = request.POST.get('last_name', request.user.last_name)
            request.user.save()

            self.object.headline = request.POST.get('headline', '')
            self.object.save()
            messages.success(request, 'Basic information updated!')

        elif section == 'about':
            self.object.bio = request.POST.get('bio', '')
            self.object.save()
            messages.success(request, 'About section updated!')

        elif section == 'education':
            self.object.institution = request.POST.get('institution', '')
            self.object.field_of_study = request.POST.get('field_of_study', '')
            grad_year = request.POST.get('graduation_year')
            self.object.graduation_year = int(grad_year) if grad_year else None
            self.object.save()
            messages.success(request, 'Education updated!')

        elif section == 'skills':
            self.object.skills = request.POST.get('skills', '')
            self.object.interests = request.POST.get('interests', '')
            self.object.save()
            messages.success(request, 'Skills & interests updated!')

        elif section == 'goals':
            self.object.goals = request.POST.get('goals', '')
            self.object.save()
            messages.success(request, 'Goals updated!')

        elif section == 'social':
            self.object.linkedin_url = request.POST.get('linkedin_url', '')
            self.object.github_url = request.POST.get('github_url', '')
            self.object.portfolio_url = request.POST.get('portfolio_url', '')
            self.object.save()
            messages.success(request, 'Social links updated!')

        elif section == 'contact':
            request.user.phone = request.POST.get('phone', '')
            request.user.save()
            messages.success(request, 'Contact info updated!')

        elif section == 'cv':
            cv = request.FILES.get('cv')
            if cv:
                self.object.cv = cv
                self.object.save()
                messages.success(request, 'CV uploaded!')

        else:
            # Full form submission (legacy support)
            return super().post(request, *args, **kwargs)

        return redirect('profiles:student_edit')


class MentorProfileEditView(LoginRequiredMixin, UpdateView):
    """
    Edit mentor profile - now supports section-based editing
    """
    model = MentorProfile
    template_name = 'profiles/mentor_edit.html'
    fields = [
        'bio', 'headline', 'expertise', 'skills',
        'experience_years', 'company', 'job_title',
        'is_available', 'max_mentees', 'session_duration',
        'hourly_rate', 'linkedin_url', 'twitter_url', 'github_url', 'website_url'
    ]
    success_url = reverse_lazy('profiles:mentor_edit')

    def get_object(self):
        profile, created = MentorProfile.objects.get_or_create(
            user=self.request.user,
            defaults={'expertise': 'General', 'skills': ''}
        )
        return profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_object()

        # Add stats
        from mentorship.models import MentorshipRequest
        context['followers_count'] = self.request.user.followers.count()
        context['active_mentees'] = MentorshipRequest.objects.filter(
            mentor=self.request.user,
            status__in=['approved', 'in_progress']
        ).count()
        context['sessions_completed'] = MentorshipRequest.objects.filter(
            mentor=self.request.user,
            status='completed'
        ).count()

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        section = request.POST.get('section', 'all')

        # Handle based on section
        if section == 'photo':
            avatar = request.FILES.get('avatar')
            if avatar:
                request.user.avatar = avatar
                request.user.save()
                messages.success(request, 'Profile photo updated!')

        elif section == 'basic':
            # Update user info
            request.user.first_name = request.POST.get('first_name', request.user.first_name)
            request.user.last_name = request.POST.get('last_name', request.user.last_name)
            request.user.save()

            # Update profile info
            self.object.headline = request.POST.get('headline', '')
            self.object.job_title = request.POST.get('job_title', '')
            self.object.company = request.POST.get('company', '')
            exp_years = request.POST.get('experience_years')
            self.object.experience_years = int(exp_years) if exp_years else None
            self.object.save()
            messages.success(request, 'Basic information updated!')

        elif section == 'about':
            self.object.bio = request.POST.get('bio', '')
            self.object.save()
            messages.success(request, 'About section updated!')

        elif section == 'skills':
            self.object.expertise = request.POST.get('expertise', '')
            self.object.skills = request.POST.get('skills', '')
            self.object.save()
            messages.success(request, 'Expertise & skills updated!')

        elif section == 'social':
            self.object.linkedin_url = request.POST.get('linkedin_url', '')
            self.object.twitter_url = request.POST.get('twitter_url', '')
            self.object.github_url = request.POST.get('github_url', '')
            self.object.website_url = request.POST.get('website_url', '')
            self.object.save()
            messages.success(request, 'Social links updated!')

        elif section == 'availability':
            self.object.is_available = request.POST.get('is_available') == 'on'
            duration = request.POST.get('session_duration')
            self.object.session_duration = int(duration) if duration else 60
            max_mentees = request.POST.get('max_mentees')
            self.object.max_mentees = int(max_mentees) if max_mentees else 5
            rate = request.POST.get('hourly_rate')
            self.object.hourly_rate = float(rate) if rate else None
            self.object.save()
            messages.success(request, 'Availability settings updated!')

        elif section == 'location':
            # Location info
            self.object.city = request.POST.get('city', '')
            self.object.country = request.POST.get('country', 'Rwanda')
            self.object.workplace_address = request.POST.get('workplace_address', '')

            # Education background
            self.object.diploma = request.POST.get('diploma', '')
            self.object.educational_institution = request.POST.get('educational_institution', '')

            # Observation internship settings
            min_days = request.POST.get('min_internship_days')
            self.object.min_internship_days = int(min_days) if min_days else 1
            max_days = request.POST.get('max_internship_days')
            self.object.max_internship_days = int(max_days) if max_days else 5

            # Mentorship types
            self.object.accepts_in_person = request.POST.get('accepts_in_person') == 'true'
            self.object.accepts_virtual = request.POST.get('accepts_virtual') == 'true'

            self.object.save()
            messages.success(request, 'Location & observation internship settings updated!')

        elif section == 'contact':
            request.user.phone = request.POST.get('phone', '')
            request.user.save()
            messages.success(request, 'Contact info updated!')

        else:
            # Full form submission (legacy support)
            return super().post(request, *args, **kwargs)

        return redirect('profiles:mentor_edit')


@login_required
def follow_user(request, user_id):
    """
    Follow a user (typically a mentor)
    """
    user_to_follow = get_object_or_404(User, id=user_id)

    if user_to_follow == request.user:
        return JsonResponse({'error': 'You cannot follow yourself'}, status=400)

    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        followed=user_to_follow
    )

    if created:
        # Create notification
        try:
            from notifications.models import Notification
            Notification.objects.create(
                recipient=user_to_follow,
                sender=request.user,
                notification_type='follow',
                message=f'{request.user.get_full_name()} started following you'
            )
        except Exception:
            pass

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'following': True,
            'followers_count': user_to_follow.followers.count()
        })

    messages.success(request, f'You are now following {user_to_follow.get_full_name()}')
    return redirect(request.META.get('HTTP_REFERER', 'core:home'))


@login_required
def unfollow_user(request, user_id):
    """
    Unfollow a user
    """
    user_to_unfollow = get_object_or_404(User, id=user_id)

    Follow.objects.filter(
        follower=request.user,
        followed=user_to_unfollow
    ).delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'following': False,
            'followers_count': user_to_unfollow.followers.count()
        })

    messages.info(request, f'You have unfollowed {user_to_unfollow.get_full_name()}')
    return redirect(request.META.get('HTTP_REFERER', 'core:home'))


class FollowersListView(LoginRequiredMixin, ListView):
    """
    List of users following the current user
    """
    template_name = 'profiles/followers.html'
    context_object_name = 'followers'
    paginate_by = 20

    def get_queryset(self):
        return Follow.objects.filter(
            followed=self.request.user
        ).select_related('follower')


class FollowingListView(LoginRequiredMixin, ListView):
    """
    List of users the current user is following
    """
    template_name = 'profiles/following.html'
    context_object_name = 'following'
    paginate_by = 20

    def get_queryset(self):
        return Follow.objects.filter(
            follower=self.request.user
        ).select_related('followed')
