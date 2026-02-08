"""
Sessions App Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone

from accounts.models import User
from .models import Session, Availability


class SessionListView(LoginRequiredMixin, ListView):
    """List user's sessions"""
    template_name = 'sessions_app/list.html'
    context_object_name = 'sessions'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        if user.is_mentor:
            return Session.objects.filter(mentor=user).select_related('student')
        return Session.objects.filter(student=user).select_related('mentor')


class SessionDetailView(LoginRequiredMixin, DetailView):
    """View session details"""
    model = Session
    template_name = 'sessions_app/detail.html'
    context_object_name = 'session'

    def get_queryset(self):
        user = self.request.user
        return Session.objects.filter(Q(mentor=user) | Q(student=user))


class BookSessionView(LoginRequiredMixin, CreateView):
    """Book a session with a mentor"""
    model = Session
    template_name = 'sessions_app/book.html'
    fields = ['title', 'description', 'scheduled_time']
    success_url = reverse_lazy('sessions_app:list')

    def dispatch(self, request, *args, **kwargs):
        self.mentor = get_object_or_404(User, pk=kwargs['mentor_id'], role='mentor')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mentor'] = self.mentor
        context['availabilities'] = Availability.objects.filter(
            mentor=self.mentor, is_active=True
        )
        return context

    def form_valid(self, form):
        form.instance.student = self.request.user
        form.instance.mentor = self.mentor
        
        try:
            form.instance.duration = self.mentor.mentor_profile.session_duration
        except Exception:
            form.instance.duration = 60
        
        response = super().form_valid(form)
        
        # Notify mentor
        try:
            from notifications.models import Notification
            Notification.objects.create(
                recipient=self.mentor,
                sender=self.request.user,
                notification_type='session_booked',
                message=f'{self.request.user.get_full_name()} booked a session with you.'
            )
        except Exception:
            pass
        
        messages.success(self.request, 'Session booked successfully!')
        return response


@login_required
def cancel_session(request, pk):
    """Cancel a session"""
    session = get_object_or_404(Session, pk=pk)
    if session.mentor != request.user and session.student != request.user:
        messages.error(request, 'You cannot cancel this session.')
        return redirect('sessions_app:list')
    
    session.cancel()
    
    # Notify the other party
    recipient = session.student if request.user == session.mentor else session.mentor
    try:
        from notifications.models import Notification
        Notification.objects.create(
            recipient=recipient,
            sender=request.user,
            notification_type='session_cancelled',
            message=f'Session "{session.title}" has been cancelled.'
        )
    except Exception:
        pass
    
    messages.info(request, 'Session cancelled.')
    return redirect('sessions_app:list')


@login_required
def complete_session(request, pk):
    """Mark session as completed (mentor only)"""
    session = get_object_or_404(Session, pk=pk, mentor=request.user)
    session.complete()
    messages.success(request, 'Session marked as completed.')
    return redirect('sessions_app:list')


class AvailabilityListView(LoginRequiredMixin, ListView):
    """List mentor's availability"""
    template_name = 'sessions_app/availability.html'
    context_object_name = 'availabilities'

    def get_queryset(self):
        return Availability.objects.filter(mentor=self.request.user)


class AddAvailabilityView(LoginRequiredMixin, CreateView):
    """Add availability slot"""
    model = Availability
    template_name = 'sessions_app/add_availability.html'
    fields = ['day_of_week', 'start_time', 'end_time']
    success_url = reverse_lazy('sessions_app:availability')

    def form_valid(self, form):
        form.instance.mentor = self.request.user
        messages.success(self.request, 'Availability added!')
        return super().form_valid(form)


@login_required
def delete_availability(request, pk):
    """Delete an availability slot"""
    availability = get_object_or_404(Availability, pk=pk, mentor=request.user)
    availability.delete()
    messages.success(request, 'Availability removed.')
    return redirect('sessions_app:availability')


class MentorCalendarView(TemplateView):
    """View mentor's calendar/availability"""
    template_name = 'sessions_app/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mentor = get_object_or_404(User, pk=kwargs['mentor_id'], role='mentor')
        context['mentor'] = mentor
        context['availabilities'] = Availability.objects.filter(mentor=mentor, is_active=True)
        
        # Get upcoming sessions
        if self.request.user.is_authenticated:
            context['booked_sessions'] = Session.objects.filter(
                mentor=mentor,
                status='scheduled',
                scheduled_time__gte=timezone.now()
            )
        return context
