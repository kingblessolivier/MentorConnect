from django.contrib.auth.decorators import login_required

@login_required
def api_slot_detail(request, pk):
    """Return JSON details for a single availability slot."""
    slot = get_object_or_404(MentorAvailability, pk=pk)
    data = {
        'id': slot.id,
        'mentor': slot.mentor.get_full_name() if hasattr(slot.mentor, 'get_full_name') else str(slot.mentor),
        'date': slot.date.isoformat(),
        'end_date': slot.end_date.isoformat() if slot.end_date else None,
        'start_time': slot.start_time.strftime('%H:%M'),
        'end_time': slot.end_time.strftime('%H:%M'),
        'title': slot.title,
        'description': slot.description,
        'location_type': slot.get_location_type_display() if hasattr(slot, 'get_location_type_display') else slot.location_type,
        'location_address': slot.location_address,
        'is_booked': slot.is_booked,
        'max_bookings': slot.max_bookings,
        'current_bookings': slot.current_bookings,
        'spots_left': slot.max_bookings - slot.current_bookings,
    }
    return JsonResponse(data)
"""
Mentorship App Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.db.models import Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import calendar
import json

from accounts.models import User
from profiles.models import MentorProfile
from .models import MentorshipRequest, Review, MentorAvailability



class MentorSearchView(LoginRequiredMixin, ListView):
    """
    Enhanced Mentor Search and Filter View
    Provides comprehensive filtering, sorting, and search capabilities
    """
    template_name = 'mentorship/search.html'
    context_object_name = 'mentors'
    paginate_by = 12

    def get_queryset(self):
        """Show all available mentors, ignoring filters (for debugging)."""
        return MentorProfile.objects.filter(
            is_available=True,
            user__is_active=True,
            profile_completed=True
        ).select_related('user').order_by('-is_featured', '-rating', '-created_at')

    def get_context_data(self, **kwargs):
        """Build context with filters, stats, and recommendations"""
        context = super().get_context_data(**kwargs)

        # Current filter values
        context['search'] = self.request.GET.get('q', '')
        context['skills'] = self.request.GET.get('skills', '')
        context['expertise'] = self.request.GET.get('expertise', '')
        context['location'] = self.request.GET.get('location', '')
        context['min_rating'] = self.request.GET.get('min_rating', '')
        context['min_experience'] = self.request.GET.get('min_experience', '')
        context['price'] = self.request.GET.get('price', '')
        context['session_type'] = self.request.GET.get('session_type', '')
        context['sort'] = self.request.GET.get('sort', '-rating')

        # Get popular skills
        context['popular_skills'] = self._get_popular_skills()

        # Get expertise areas
        context['expertise_areas'] = self._get_expertise_areas()

        # Get unique locations
        context['locations'] = self._get_unique_locations()

        # Featured mentors
        context['featured_mentors'] = MentorProfile.objects.filter(
            is_available=True,
            is_featured=True,
            profile_completed=True
        ).select_related('user').order_by('-rating')[:4]

        # Stats
        context['total_mentors'] = MentorProfile.objects.filter(
            is_available=True,
            profile_completed=True
        ).count()
        context['total_sessions'] = MentorshipRequest.objects.filter(
            status='completed'
        ).count()

        # Selected skills as list
        context['selected_skills'] = [
            s.strip() for s in context['skills'].split(',') if s.strip()
        ]

        # Whether filters are active
        context['has_active_filters'] = bool(
            context['search'] or context['skills'] or context['expertise'] or
            context['location'] or context['min_rating'] or context['min_experience'] or
            context['price'] or context['session_type']
        )

        return context

    def _get_popular_skills(self, limit=20):
        """Get most popular skills across mentors"""
        from collections import Counter
        all_skills = []
        for mentor in MentorProfile.objects.filter(
            is_available=True, profile_completed=True
        ).values_list('skills', flat=True):
            if mentor:
                all_skills.extend([s.strip() for s in mentor.split(',') if s.strip()])

        skill_counts = Counter(all_skills)
        return [skill for skill, count in skill_counts.most_common(limit)]

    def _get_expertise_areas(self, limit=15):
        """Get unique expertise areas"""
        expertise_areas = MentorProfile.objects.filter(
            is_available=True, profile_completed=True
        ).values_list('expertise', flat=True).distinct()
        return sorted([e for e in expertise_areas if e])[:limit]

    def _get_unique_locations(self, limit=20):
        """Get unique mentor locations"""
        locations = MentorProfile.objects.filter(
            is_available=True,
            profile_completed=True,
            city__isnull=False
        ).exclude(
            city__exact=''
        ).values_list('city', flat=True).distinct()
        return sorted([l for l in locations if l])[:limit]


class CreateMentorshipRequestView(LoginRequiredMixin, CreateView):
    """Create an observation internship request"""
    model = MentorshipRequest
    template_name = 'mentorship/create_request.html'
    fields = ['subject', 'message', 'goals', 'requested_days', 'request_type', 'current_education', 'field_of_interest']
    success_url = reverse_lazy('mentorship:requests')

    def dispatch(self, request, *args, **kwargs):
        self.mentor = get_object_or_404(User, pk=kwargs['mentor_id'], role='mentor')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mentor'] = self.mentor
        return context

    def form_valid(self, form):
        form.instance.student = self.request.user
        form.instance.mentor = self.mentor

        # Handle NDA agreement
        if self.request.POST.get('nda_agreed'):
            form.instance.nda_agreed = True
            form.instance.nda_agreed_at = timezone.now()

        # Check for existing pending request
        existing = MentorshipRequest.objects.filter(
            student=self.request.user, mentor=self.mentor, status='pending'
        ).exists()
        if existing:
            messages.warning(self.request, 'You already have a pending request with this professional.')
            return redirect('mentorship:requests')

        response = super().form_valid(form)

        # Notify mentor
        try:
            from notifications.models import Notification
            Notification.objects.create(
                recipient=self.mentor,
                sender=self.request.user,
                notification_type='new_request',
                message=f'{self.request.user.get_full_name()} sent you an observation internship request for {form.instance.requested_days} day(s).'
            )
        except Exception:
            pass

        messages.success(self.request, 'Your observation internship request has been sent!')
        return response


class MentorshipRequestListView(LoginRequiredMixin, ListView):
    """List user's mentorship requests"""
    template_name = 'mentorship/request_list.html'
    context_object_name = 'requests'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        if user.is_mentor:
            return MentorshipRequest.objects.filter(mentor=user).select_related('student')
        return MentorshipRequest.objects.filter(student=user).select_related('mentor')


class MentorshipRequestDetailView(LoginRequiredMixin, DetailView):
    """View mentorship request details"""
    model = MentorshipRequest
    template_name = 'mentorship/request_detail.html'
    context_object_name = 'request'

    def get_queryset(self):
        user = self.request.user
        return MentorshipRequest.objects.filter(Q(student=user) | Q(mentor=user))


@login_required
def approve_request(request, pk):
    """Approve a mentorship request"""
    mentorship = get_object_or_404(MentorshipRequest, pk=pk, mentor=request.user, status='pending')
    response_text = request.POST.get('response', '')
    mentorship.approve(response_text)
    messages.success(request, 'Request approved!')
    return redirect('mentorship:request_list')


@login_required
def reject_request(request, pk):
    """Reject a mentorship request"""
    mentorship = get_object_or_404(MentorshipRequest, pk=pk, mentor=request.user, status='pending')
    response_text = request.POST.get('response', '')
    mentorship.reject(response_text)
    messages.info(request, 'Request rejected.')
    return redirect('mentorship:request_list')


@login_required
def cancel_request(request, pk):
    """Cancel a mentorship request (by student)"""
    mentorship = get_object_or_404(MentorshipRequest, pk=pk, student=request.user, status='pending')
    mentorship.status = 'cancelled'
    mentorship.save()
    messages.info(request, 'Request cancelled.')
    return redirect('mentorship:request_list')


class CreateReviewView(LoginRequiredMixin, CreateView):
    """Create a review for a mentor"""
    model = Review
    template_name = 'mentorship/create_review.html'
    fields = ['rating', 'title', 'content']

    def dispatch(self, request, *args, **kwargs):
        self.mentor = get_object_or_404(User, pk=kwargs['mentor_id'], role='mentor')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mentor'] = self.mentor
        return context

    def get_success_url(self):
        # Redirect back to the referring page or search page
        referer = self.request.META.get('HTTP_REFERER', '')
        if 'search' in referer:
            return reverse_lazy('mentorship:search')
        return reverse_lazy('profiles:mentor_detail', kwargs={'pk': self.mentor.id})

    def form_valid(self, form):
        # Check if user already reviewed this mentor
        existing_review = Review.objects.filter(
            student=self.request.user,
            mentor=self.mentor
        ).first()

        if existing_review:
            # Update existing review instead
            existing_review.rating = form.cleaned_data['rating']
            existing_review.title = form.cleaned_data.get('title', '')
            existing_review.content = form.cleaned_data['content']
            existing_review.save()
            messages.success(self.request, 'Your review has been updated!')
            return redirect(self.get_success_url())

        form.instance.student = self.request.user
        form.instance.mentor = self.mentor

        # Handle AJAX request
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            response = super().form_valid(form)
            return JsonResponse({
                'success': True,
                'message': 'Thank you for your review!',
                'rating': form.instance.rating
            })

        messages.success(self.request, 'Thank you for your review!')
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        return super().form_invalid(form)


class MentorReviewsView(ListView):
    """View all reviews for a mentor"""
    template_name = 'mentorship/mentor_reviews.html'
    context_object_name = 'reviews'
    paginate_by = 10

    def get_queryset(self):
        return Review.objects.filter(mentor_id=self.kwargs['mentor_id']).select_related('student')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mentor'] = get_object_or_404(User, pk=self.kwargs['mentor_id'])
        context['average_rating'] = Review.objects.filter(
            mentor_id=self.kwargs['mentor_id']
        ).aggregate(Avg('rating'))['rating__avg']
        return context


# ============ MENTOR AVAILABILITY VIEWS ============

class MentorAvailabilityView(LoginRequiredMixin, TemplateView):
    """Mentor's availability calendar management"""
    template_name = 'mentorship/availability_calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get month/year from query params or use current
        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))

        # Generate calendar data
        cal = calendar.Calendar(firstweekday=0)  # Monday first
        month_days = cal.monthdayscalendar(year, month)

        # Get availability slots for this month
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()

        availabilities = MentorAvailability.objects.filter(
            mentor=self.request.user,
            date__gte=start_date,
            date__lt=end_date
        )

        # Create a dict of date -> list of slots
        availability_by_date = {}
        for slot in availabilities:
            date_str = slot.date.isoformat()
            if date_str not in availability_by_date:
                availability_by_date[date_str] = []
            availability_by_date[date_str].append(slot)

        # Navigation
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1

        context.update({
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'month_days': month_days,
            'availability_by_date': availability_by_date,
            'today': timezone.now().date(),
            'prev_month': prev_month,
            'prev_year': prev_year,
            'next_month': next_month,
            'next_year': next_year,
            'weekdays': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        })
        return context


@login_required
def add_availability(request):
    """Add a new availability slot"""
    if request.method == 'POST':
        date_str = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        max_bookings = int(request.POST.get('max_bookings', 1))

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start = datetime.strptime(start_time, '%H:%M').time()
            end = datetime.strptime(end_time, '%H:%M').time()

            MentorAvailability.objects.create(
                mentor=request.user,
                date=date,
                start_time=start,
                end_time=end,
                title=title,
                description=description,
                max_bookings=max_bookings
            )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            messages.success(request, 'Availability slot added!')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            messages.error(request, f'Error: {e}')

        return redirect('mentorship:availability')

    return redirect('mentorship:availability')


@login_required
def delete_availability(request, pk):
    """Delete an availability slot"""
    slot = get_object_or_404(MentorAvailability, pk=pk, mentor=request.user)

    if slot.current_bookings > 0:
        messages.warning(request, 'Cannot delete - this slot has bookings.')
    else:
        slot.delete()
        messages.success(request, 'Availability slot deleted.')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('mentorship:availability')


@login_required
def get_availability_slots(request, mentor_id):
    """Get availability slots for a mentor (JSON API)"""
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))

    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()

    slots = MentorAvailability.objects.filter(
        mentor_id=mentor_id,
        date__gte=start_date,
        date__lt=end_date
    ).values('id', 'date', 'start_time', 'end_time', 'title', 'description', 'is_booked', 'max_bookings', 'current_bookings')

    data = []
    for slot in slots:
        data.append({
            'id': slot['id'],
            'date': slot['date'].isoformat(),
            'start_time': slot['start_time'].strftime('%H:%M'),
            'end_time': slot['end_time'].strftime('%H:%M'),
            'title': slot['title'],
            'description': slot['description'],
            'is_available': slot['current_bookings'] < slot['max_bookings'],
            'spots_left': slot['max_bookings'] - slot['current_bookings']
        })

    return JsonResponse({'slots': data})


# ============ SCHEDULING VIEWS ============

@login_required
def schedule_session(request, pk):
    """Schedule a mentorship session (select time slot)"""
    mentorship = get_object_or_404(
        MentorshipRequest,
        pk=pk,
        student=request.user,
        status='approved'
    )

    if request.method == 'POST':
        slot_id = request.POST.get('slot_id')
        meeting_link = request.POST.get('meeting_link', '')

        if slot_id:
            slot = get_object_or_404(MentorAvailability, pk=slot_id, mentor=mentorship.mentor)
            if slot.is_available:
                mentorship.schedule(availability_slot=slot, meeting_link=meeting_link)
                messages.success(request, f'Session scheduled for {slot.date} at {slot.start_time}!')
            else:
                messages.error(request, 'This slot is no longer available.')
        return redirect('mentorship:request_detail', pk=pk)

    # GET - show available slots
    today = timezone.now().date()
    available_slots = MentorAvailability.objects.filter(
        mentor=mentorship.mentor,
        date__gte=today,
        current_bookings__lt=models.F('max_bookings')
    ).order_by('date', 'start_time')

    return render(request, 'mentorship/schedule_session.html', {
        'mentorship': mentorship,
        'available_slots': available_slots
    })


@login_required
def start_session(request, pk):
    """Mark session as started (in progress)"""
    mentorship = get_object_or_404(
        MentorshipRequest,
        pk=pk,
        mentor=request.user,
        status='scheduled'
    )
    mentorship.start_session()
    messages.success(request, 'Session marked as in progress!')
    return redirect('mentorship:request_detail', pk=pk)


@login_required
def complete_session(request, pk):
    """Mark session as completed"""
    mentorship = get_object_or_404(
        MentorshipRequest,
        pk=pk,
        mentor=request.user,
        status='in_progress'
    )
    notes = request.POST.get('notes', '')
    mentorship.complete(notes)
    messages.success(request, 'Session marked as completed!')
    return redirect('mentorship:request_detail', pk=pk)


# ============ STUDENT VIEW OF MENTOR CALENDAR ============

class MentorCalendarView(TemplateView):
    """View mentor's availability calendar (for students)"""
    template_name = 'mentorship/mentor_calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mentor = get_object_or_404(User, pk=self.kwargs['mentor_id'], role='mentor')

        # Get month/year from query params or use current
        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))

        # Generate calendar data
        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(year, month)

        # Get availability slots
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()

        availabilities = MentorAvailability.objects.filter(
            mentor=mentor,
            date__gte=start_date,
            date__lt=end_date
        )

        availability_by_date = {}
        for slot in availabilities:
            date_str = slot.date.isoformat()
            if date_str not in availability_by_date:
                availability_by_date[date_str] = []
            availability_by_date[date_str].append(slot)

        # Navigation
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1

        context.update({
            'mentor': mentor,
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'month_days': month_days,
            'availability_by_date': availability_by_date,
            'today': timezone.now().date(),
            'prev_month': prev_month,
            'prev_year': prev_year,
            'next_month': next_month,
            'next_year': next_year,
            'weekdays': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        })
        return context


# Need to import models for F expression
from django.db import models


@login_required
def api_search_mentors(request):
    """
    AJAX API endpoint for mentor search with filters
    Returns JSON list of mentors
    """
    from django.core.paginator import Paginator

    search_view = MentorSearchView()
    search_view.request = request

    mentors = search_view.get_queryset()

    # Serialize mentor data
    mentor_data = []
    for mentor in mentors[:20]:  # Limit to 20 for AJAX
        mentor_data.append({
            'id': mentor.user.id,
            'name': mentor.user.get_full_name(),
            'headline': mentor.headline or mentor.expertise,
            'expertise': mentor.expertise,
            'rating': float(mentor.rating),
            'total_reviews': mentor.total_reviews,
            'experience_years': mentor.experience_years,
            'is_featured': mentor.is_featured,
            'is_available': mentor.is_available,
            'hourly_rate': float(mentor.hourly_rate),
            'city': mentor.city,
            'skills': mentor.get_skills_list()[:3],
        })

    return JsonResponse({
        'success': True,
        'count': mentors.count(),
        'mentors': mentor_data
    })


@login_required
def get_filter_options(request):
    """
    Get available filter options for search page
    """
    search_view = MentorSearchView()
    search_view.request = request

    return JsonResponse({
        'success': True,
        'expertise_areas': search_view._get_expertise_areas(),
        'skills': search_view._get_popular_skills(),
        'locations': search_view._get_unique_locations(),
    })

