"""
Accounts App Views
Authentication views: Login, Signup, Logout, Password Reset
"""

from django.shortcuts import render, redirect
from django.views.generic import CreateView, FormView, TemplateView
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse

from .forms import (
    LoginForm,
    StudentRegistrationForm,
    MentorRegistrationForm,
    UserUpdateForm
)
from .models import User
from core.models import ActivityLog


class CustomLoginView(LoginView):
    """
    Modern login view with remember me functionality
    """
    template_name = 'accounts/login.html'
    form_class = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        # Redirect based on user role
        user = self.request.user
        if user.is_admin_user:
            return reverse_lazy('dashboard:admin_dashboard')
        elif user.is_mentor:
            return reverse_lazy('dashboard:mentor_dashboard')
        return reverse_lazy('dashboard:student_dashboard')

    def form_valid(self, form):
        # Handle remember me
        remember_me = form.cleaned_data.get('remember_me', False)
        if not remember_me:
            self.request.session.set_expiry(0)

        # Log the activity
        response = super().form_valid(form)

        try:
            ActivityLog.objects.create(
                user=self.request.user,
                action='login',
                description=f'User {self.request.user.email} logged in',
                ip_address=self.get_client_ip(),
            )
        except Exception:
            pass

        messages.success(self.request, f"Welcome back, {self.request.user.first_name}!")
        return response

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')


class CustomLogoutView(LogoutView):
    """
    Logout view with activity logging
    """
    http_method_names = ['get', 'post', 'options']

    def get_next_page(self):
        return reverse_lazy('core:home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            try:
                ActivityLog.objects.create(
                    user=request.user,
                    action='logout',
                    description=f'User {request.user.email} logged out',
                )
            except Exception:
                pass
            messages.info(request, 'You have been logged out successfully.')
        return super().dispatch(request, *args, **kwargs)


class StudentSignupView(CreateView):
    """
    Student registration view
    """
    template_name = 'accounts/signup_student.html'
    form_class = StudentRegistrationForm
    success_url = reverse_lazy('dashboard:student_dashboard')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)

        # Log the user in
        login(self.request, self.object)

        # Log activity
        try:
            ActivityLog.objects.create(
                user=self.object,
                action='register',
                description=f'New student registered: {self.object.email}',
            )
        except Exception:
            pass

        # Create student profile
        try:
            from profiles.models import StudentProfile
            StudentProfile.objects.get_or_create(user=self.object)
        except Exception:
            pass

        messages.success(self.request, 'Welcome to MentorConnect! Your account has been created.')
        return response


class MentorSignupView(CreateView):
    """
    Mentor registration view
    """
    template_name = 'accounts/signup_mentor.html'
    form_class = MentorRegistrationForm
    success_url = reverse_lazy('dashboard:mentor_dashboard')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)

        # Log the user in
        login(self.request, self.object)

        # Log activity
        try:
            ActivityLog.objects.create(
                user=self.object,
                action='register',
                description=f'New mentor registered: {self.object.email}',
            )
        except Exception:
            pass

        # Create mentor profile with form data
        try:
            from profiles.models import MentorProfile
            MentorProfile.objects.get_or_create(
                user=self.object,
                defaults={
                    'expertise': form.cleaned_data.get('expertise', ''),
                    'experience_years': form.cleaned_data.get('experience_years', 0),
                }
            )
        except Exception:
            pass

        messages.success(self.request, 'Welcome to MentorConnect! Your mentor account has been created.')
        return response


class SignupChoiceView(TemplateView):
    """
    Page to choose between student and mentor signup
    """
    template_name = 'accounts/signup_choice.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)


class ProfileSettingsView(LoginRequiredMixin, FormView):
    """
    User profile settings view
    """
    template_name = 'accounts/settings.html'
    form_class = UserUpdateForm
    success_url = reverse_lazy('accounts:settings')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Your profile has been updated successfully.')
        return super().form_valid(form)


def check_email(request):
    """
    AJAX endpoint to check if email is available
    """
    email = request.GET.get('email', '')
    exists = User.objects.filter(email=email).exists()
    return JsonResponse({'available': not exists})
