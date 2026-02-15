from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import CreateView, TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Availability, Session
from .forms import AvailabilityForm, SessionRequestForm
from .forms import SessionCreateForm
from django.contrib.auth import get_user_model
User = get_user_model()
from django.utils import timezone



class AddAvailabilityView(LoginRequiredMixin, CreateView):
    model = Availability
    form_class = AvailabilityForm
    template_name = 'sessions_app/add_availability.html'
    success_url = reverse_lazy('sessions_app:mentor-schedule')

    def form_valid(self, form):
        av = form.save(commit=False)
        av.mentor = self.request.user
        av.save()
        messages.success(self.request, 'Availability added.')
        return super().form_valid(form)


class MentorScheduleView(LoginRequiredMixin, TemplateView):
    template_name = 'sessions_app/calendar.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        mentor_id = self.kwargs.get('mentor_id')
        mentor = get_object_or_404(User, pk=mentor_id)
        ctx['mentor'] = mentor
        ctx['mentor_id'] = mentor_id
        return ctx


class EventsJsonView(View):
    def get(self, request, mentor_id):
        mentor_id = int(mentor_id)
        # Pull availabilities and sessions for the mentor
        avail_qs = Availability.objects.filter(mentor_id=mentor_id, is_active=True)
        sessions_qs = Session.objects.filter(mentor_id=mentor_id)

        events = []
        for av in avail_qs:
            if av.start and av.end:
                events.append({
                    'id': f"avail-{av.id}",
                    'title': f"Available - {av.location_name or 'Online'}",
                    'start': av.start.isoformat(),
                    'end': av.end.isoformat(),
                    'color': 'green',
                    'extendedProps': {
                        'type': 'availability',
                        'availability_id': av.id,
                        'location_name': av.location_name,
                        'address': av.address,
                        'session_type': av.session_type,
                        'is_booked': av.is_booked,
                    }
                })

        for s in sessions_qs:
            if s.start and s.end:
                events.append({
                    'id': f"session-{s.id}",
                    'title': f"{s.title or 'Booked'} - {s.location_name or s.session_type}",
                    'start': s.start.isoformat(),
                    'end': s.end.isoformat(),
                    'color': 'blue' if s.status in ('approved', 'pending') else 'gray',
                    'extendedProps': {
                        'type': 'session',
                        'session_id': s.id,
                        'status': s.status,
                        'student': s.student.get_full_name(),
                        'location_name': s.location_name,
                        'address': s.address,
                    }
                })

        return JsonResponse(events, safe=False)


class BookAvailabilityView(LoginRequiredMixin, View):
    def post(self, request, availability_id):
        av = get_object_or_404(Availability, id=availability_id, is_active=True)
        # prevent booking if already booked
        if av.is_booked:
            messages.error(request, 'This slot is already booked.')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        form = SessionRequestForm(request.POST)
        if form.is_valid():
            s = form.save(commit=False)
            s.student = request.user
            s.mentor = av.mentor
            s.availability = av
            s.start = av.start
            s.end = av.end
            s.session_type = av.session_type or 'online'
            s.location_name = av.location_name
            s.address = av.address
            s.status = 'pending'
            s.save()
            # Notify mentor
            try:
                from notifications.models import Notification
                Notification.objects.create(
                    recipient=av.mentor,
                    sender=request.user,
                    notification_type='session_requested',
                    message=f'{request.user.get_full_name()} requested a session with you.'
                )
            except Exception:
                pass
            messages.success(request, 'Session request sent to mentor.')
            return redirect('sessions_app:student-schedule')
        messages.error(request, 'Invalid request.')
        return redirect(request.META.get('HTTP_REFERER', '/'))


class ApproveSessionView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        s = get_object_or_404(Session, id=session_id)
        if request.user != s.mentor:
            return HttpResponseForbidden()
        try:
            s.approve(by_user=request.user)
            messages.success(request, 'Session approved — slot marked as booked.')
            # Notify student
            try:
                from notifications.models import Notification
                Notification.objects.create(
                    recipient=s.student,
                    sender=request.user,
                    notification_type='session_approved',
                    message=f'Your session "{s.title}" has been approved by {request.user.get_full_name()}.'
                )
            except Exception:
                pass
        except Exception as e:
            messages.error(request, str(e))
        return redirect(request.META.get('HTTP_REFERER', '/'))


class RejectSessionView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        s = get_object_or_404(Session, id=session_id)
        if request.user != s.mentor:
            return HttpResponseForbidden()
        s.reject()
        messages.success(request, 'Session rejected.')
        # Notify student
        try:
            from notifications.models import Notification
            Notification.objects.create(
                recipient=s.student,
                sender=request.user,
                notification_type='session_rejected',
                message=f'Your session "{s.title}" has been rejected by {request.user.get_full_name()}.'
            )
        except Exception:
            pass
        return redirect(request.META.get('HTTP_REFERER', '/'))


class StartSessionView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        s = get_object_or_404(Session, id=session_id)
        if request.user != s.mentor:
            return HttpResponseForbidden()
        # Only allow starting for physical sessions
        if s.session_type != 'physical':
            messages.error(request, 'Only in-person sessions can be started this way.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        if s.status != 'approved':
            messages.error(request, 'Session must be approved to start.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        s.status = 'in_progress'
        s.save()
        messages.success(request, 'Session marked as in progress.')
        # Notify student
        try:
            from notifications.models import Notification
            Notification.objects.create(
                recipient=s.student,
                sender=request.user,
                notification_type='session_started',
                message=f'Session "{s.title}" has started.'
            )
        except Exception:
            pass
        return redirect(request.META.get('HTTP_REFERER', '/'))


class CompleteSessionView(LoginRequiredMixin, View):
    def post(self, request, session_id):
        s = get_object_or_404(Session, id=session_id)
        if request.user != s.mentor:
            return HttpResponseForbidden()
        if s.session_type != 'physical':
            messages.error(request, 'Only in-person sessions can be completed this way.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        if s.status not in ('approved', 'in_progress'):
            messages.error(request, 'Session must be approved or in progress to complete.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        s.status = 'completed'
        s.save()
        # mark availability booked if present
        if s.availability:
            s.availability.is_booked = True
            s.availability.save()
        messages.success(request, 'Session marked as completed.')
        # Notify student
        try:
            from notifications.models import Notification
            Notification.objects.create(
                recipient=s.student,
                sender=request.user,
                notification_type='session_completed',
                message=f'Session "{s.title}" has been completed.'
            )
        except Exception:
            pass
        return redirect(request.META.get('HTTP_REFERER', '/'))


class StudentScheduleView(LoginRequiredMixin, TemplateView):
    template_name = 'sessions_app/student_schedule.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        sessions = Session.objects.filter(student=self.request.user).order_by('-start')
        ctx['sessions'] = sessions
        ctx['total_count'] = sessions.count()
        ctx['approved_count'] = sessions.filter(status='approved').count()
        ctx['pending_count'] = sessions.filter(status='pending').count()
        ctx['rejected_count'] = sessions.filter(status='rejected').count()
        ctx['completed_count'] = sessions.filter(status='completed').count()
        ctx['in_progress_count'] = sessions.filter(status='in_progress').count()
        return ctx


class MentorSessionsListView(LoginRequiredMixin, TemplateView):
    template_name = 'sessions_app/mentor_sessions.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['sessions'] = Session.objects.filter(mentor=self.request.user).order_by('-start')
        return ctx


class MentorCreateSessionView(LoginRequiredMixin, View):
    template_name = 'sessions_app/create_session.html'

    def get(self, request, mentor_id):
        # only allow creating sessions for yourself as mentor
        if request.user.id != int(mentor_id):
            return HttpResponseForbidden()
        form = SessionCreateForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, mentor_id):
        if request.user.id != int(mentor_id):
            return HttpResponseForbidden()
        form = SessionCreateForm(request.POST)
        if form.is_valid():
            s = form.save(commit=False)
            s.mentor = request.user
            # ensure availability not set; this is an ad-hoc session
            s.availability = None
            s.status = 'approved'
            s.save()
            # Notify student
            try:
                from notifications.models import Notification
                Notification.objects.create(
                    recipient=s.student,
                    sender=request.user,
                    notification_type='session_created',
                    message=f'{request.user.get_full_name()} created a session with you.'
                )
            except Exception:
                pass
            messages.success(request, 'Session created.')
            return redirect('sessions_app:mentor-sessions')
        return render(request, self.template_name, {'form': form})
"""
Sessions App Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, TemplateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone


from accounts.models import User
from .models import Session, Availability
from .forms import SessionRescheduleForm


class SessionListView(LoginRequiredMixin, ListView):
    """List user's sessions"""
    template_name = 'sessions_app/list.html'
    context_object_name = 'sessions'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        if user.is_mentor:
            qs = Session.objects.filter(mentor=user).select_related('student')
        else:
            qs = Session.objects.filter(student=user).select_related('mentor')
        
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
        
        # Search by title or description
        search = self.request.GET.get('search', '')
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))
        
        return qs.order_by('-start')


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
    fields = ['title', 'description', 'start', 'end']
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
        # Ensure start/end are set; default duration from mentor profile if end missing
        try:
            default_minutes = self.mentor.mentor_profile.session_duration
        except Exception:
            default_minutes = 60
        if not form.instance.end and form.instance.start:
            from datetime import timedelta
            form.instance.end = form.instance.start + timedelta(minutes=default_minutes)
        
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


class RescheduleSessionView(LoginRequiredMixin, UpdateView):
    """Reschedule a session (update start/end, title, description)"""
    model = Session
    form_class = SessionRescheduleForm
    template_name = 'sessions_app/reschedule_session.html'
    success_url = reverse_lazy('sessions_app:list')

    def get_queryset(self):
        # Only allow rescheduling if user is mentor or student of the session
        user = self.request.user
        return Session.objects.filter(Q(mentor=user) | Q(student=user))

    def form_valid(self, form):
        session = form.save(commit=False)
        # Ensure status remains unchanged
        session.save()
        # Notify the other party
        recipient = session.student if self.request.user == session.mentor else session.mentor
        try:
            from notifications.models import Notification
            Notification.objects.create(
                recipient=recipient,
                sender=self.request.user,
                notification_type='session_rescheduled',
                message=f'Session "{session.title}" has been rescheduled.'
            )
        except Exception:
            pass
        messages.success(self.request, 'Session rescheduled successfully!')
        return super().form_valid(form)


@login_required
def complete_session(request, pk):
    """Mark session as completed (mentor only)"""
    session = get_object_or_404(Session, pk=pk, mentor=request.user)
    session.complete()
    messages.success(request, 'Session marked as completed.')
    return redirect('sessions_app:list')


@login_required
def session_ics_export(request, pk):
    """Export session to ICS calendar file"""
    session = get_object_or_404(Session, pk=pk)
    if session.mentor != request.user and session.student != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()
    from .calendar_utils import session_ics_response
    filename = f'session-{session.pk}.ics'
    return session_ics_response(session, filename)


class AvailabilityListView(LoginRequiredMixin, ListView):
    """List mentor's availability"""
    template_name = 'sessions_app/availability.html'
    context_object_name = 'availabilities'

    def get_queryset(self):
        return Availability.objects.filter(mentor=self.request.user)


class AddAvailabilityView(LoginRequiredMixin, CreateView):
    """Add availability slot (uses `AvailabilityForm` with datetime ranges)"""
    model = Availability
    form_class = AvailabilityForm
    template_name = 'sessions_app/add_availability.html'
    success_url = reverse_lazy('sessions_app:availability')

    def form_valid(self, form):
        form.instance.mentor = self.request.user
        messages.success(self.request, 'Availability added!')
        return super().form_valid(form)


class EditAvailabilityView(LoginRequiredMixin, UpdateView):
    """Edit an existing availability slot"""
    model = Availability
    form_class = AvailabilityForm
    template_name = 'sessions_app/edit_availability.html'
    success_url = reverse_lazy('sessions_app:availability')

    def get_queryset(self):
        # Ensure mentor can only edit their own availability
        return Availability.objects.filter(mentor=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Availability updated!')
        return super().form_valid(form)


@login_required
def delete_availability(request, pk):
    """Delete an availability slot"""
    availability = get_object_or_404(Availability, pk=pk, mentor=request.user)
    availability.delete()
    messages.success(request, 'Availability removed.')
    return redirect('sessions_app:availability')


class MentorCalendarView(TemplateView):
    """View mentor's calendar/availability (month grid) - reuses mentorship template."""
    template_name = 'mentorship/mentor_calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mentor = get_object_or_404(User, pk=kwargs['mentor_id'], role='mentor')

        # month/year from query params or current
        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))

        import calendar as _calendar
        from datetime import datetime, date

        cal = _calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(year, month)

        # date range for the month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        # Query availabilities whose start date is within month
        avail_qs = Availability.objects.filter(
            mentor=mentor,
            start__date__gte=start_date,
            start__date__lt=end_date,
            is_active=True,
        ).order_by('start')

        availability_by_date = {}
        for av in avail_qs:
            d = av.start.date()
            key = d.isoformat()
            slot = {
                'id': av.id,
                'date': d,
                'start_time': av.start.time(),
                'end_time': av.end.time() if av.end else None,
                'title': av.title if hasattr(av, 'title') and av.title else 'Available',
                'description': getattr(av, 'description', ''),
                'is_available': not av.is_booked,
                'spots_left': getattr(av, 'spots_left', 1),
                'max_bookings': getattr(av, 'max_bookings', 1),
                'current_bookings': getattr(av, 'current_bookings', 0),
            }
            availability_by_date.setdefault(key, []).append(slot)

        # navigation months
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1

        context.update({
            'mentor': mentor,
            'year': year,
            'month': month,
            'month_name': _calendar.month_name[month],
            'month_days': month_days,
            'availability_by_date': availability_by_date,
            'today': timezone.now().date(),
            'prev_month': prev_month,
            'prev_year': prev_year,
            'next_month': next_month,
            'next_year': next_year,
            'weekdays': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        })

        # upcoming booked sessions for the mentor
        if self.request.user.is_authenticated:
            context['booked_sessions'] = Session.objects.filter(
                mentor=mentor,
                status__in=['approved', 'pending', 'in_progress'],
                start__gte=timezone.now()
            ).order_by('start')

        return context
