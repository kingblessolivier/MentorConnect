"""
Applications App Views
Guest application, mentor actions, invitation registration
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseForbidden
from django.utils import timezone

from .models import GuestApplication, InvitationToken
from .forms import GuestApplicationForm, MentorApplicationActionForm
from .services import send_approval_email


class GuestApplicationCreateView(CreateView):
    """Guest can apply without account"""
    model = GuestApplication
    form_class = GuestApplicationForm
    template_name = 'applications/apply.html'
    success_url = reverse_lazy('applications:apply_success')

    def get_initial(self):
        initial = super().get_initial()
        mentor_id = self.kwargs.get('mentor_id')
        if mentor_id:
            from accounts.models import User
            mentor = User.objects.filter(pk=mentor_id, role='mentor').first()
            if mentor:
                initial['mentor'] = mentor
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mentor_id = self.kwargs.get('mentor_id')
        if mentor_id:
            from accounts.models import User
            mentor = User.objects.filter(pk=mentor_id, role='mentor').first()
            context['preselected_mentor'] = mentor
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            'Your application has been submitted! The mentor will review it and contact you.'
        )
        return super().form_valid(form)


class ApplySuccessView(TemplateView):
    """Thank you page after guest application"""
    template_name = 'applications/apply_success.html'


class MentorApplicationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Mentor views their applications"""
    model = GuestApplication
    template_name = 'applications/mentor_applications.html'
    context_object_name = 'applications'
    paginate_by = 10

    def test_func(self):
        return self.request.user.is_mentor

    def get_queryset(self):
        return GuestApplication.objects.filter(
            mentor=self.request.user
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        context['pending_count'] = qs.filter(status='pending').count()
        context['approved_count'] = qs.filter(status='approved').count()
        context['rejected_count'] = qs.filter(status='rejected').count()
        return context


class MentorApplicationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Mentor views single application"""
    model = GuestApplication
    template_name = 'applications/mentor_application_detail.html'
    context_object_name = 'application'

    def test_func(self):
        app = self.get_object()
        return app.mentor == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_form'] = MentorApplicationActionForm()
        return context


@login_required
def mentor_application_action(request, pk):
    """Mentor approve/reject application"""
    application = get_object_or_404(GuestApplication, pk=pk)
    if application.mentor != request.user:
        return HttpResponseForbidden()

    if application.status != 'pending':
        messages.warning(request, 'This application has already been processed.')
        return redirect('applications:mentor_applications')

    if request.method == 'POST':
        action = request.POST.get('action', '')
        feedback = request.POST.get('feedback', '').strip()

        if action == 'approve':
            application.approve(feedback=feedback)
            send_approval_email(application)
            messages.success(
                request,
                f'Application approved! An invitation email has been sent to {application.email}.'
            )
        elif action == 'reject':
            application.reject(feedback=feedback)
            messages.info(request, 'Application has been rejected.')

    return redirect('applications:mentor_applications')


def register_with_token(request, token):
    """Invitation-based registration - create account and link to application"""
    token_obj = get_object_or_404(InvitationToken, token=token)

    if not token_obj.is_valid:
        return render(request, 'applications/invitation_expired.html', {'token': token})

    application = token_obj.application

    if request.method == 'POST':
        from accounts.forms import StudentRegistrationForm
        from django.contrib.auth import get_user_model
        User = get_user_model()
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Update name from application
            parts = application.name.split()
            if parts:
                user.first_name = parts[0]
                user.last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
                user.save()

            # Create StudentProfile and link application
            from profiles.models import StudentProfile
            profile, _ = StudentProfile.objects.get_or_create(user=user)
            profile.institution = application.school
            profile.interests = application.interests
            if application.cv:
                profile.cv = application.cv
            profile.save()

            application.student = user
            application.save(update_fields=['student'])

            token_obj.used_at = timezone.now()
            token_obj.save(update_fields=['used_at'])

            from django.contrib.auth import login
            login(request, user)

            messages.success(
                request,
                'Welcome! Your account has been created. Check your dashboard for mentor feedback.'
            )
            return redirect('dashboard:student_dashboard')

        return render(request, 'applications/register_with_token.html', {
            'form': form,
            'application': application,
            'token': token,
        })

    # GET - show registration form
    from accounts.forms import StudentRegistrationForm
    initial = {
        'email': application.email,
        'first_name': application.name.split()[0] if application.name else '',
        'last_name': ' '.join(application.name.split()[1:]) if len(application.name.split()) > 1 else '',
    }
    form = StudentRegistrationForm(initial=initial)
    return render(request, 'applications/register_with_token.html', {
        'form': form,
        'application': application,
        'token': token,
    })
