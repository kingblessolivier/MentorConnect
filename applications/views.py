"""
Applications App Views
Multi-step mentorship applications, mentor view, student applications
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils import timezone

from django.conf import settings as django_settings

from django.contrib.contenttypes.models import ContentType

from .models import Application, Payment, ActivityLog, ApplicationWizardSession
from .forms import (
    ApplicationPaymentForm,
    ApplicationWizardStep1Form, ApplicationWizardStep2Form, ApplicationWizardStep3Form,
    ApplicationTrackingForm,
)


class MentorApplicationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Mentor views mentorship applications where they are the selected mentor"""
    model = Application
    template_name = 'applications/mentor_applications.html'
    context_object_name = 'applications'
    paginate_by = 10

    def test_func(self):
        return self.request.user.is_mentor

    def get_queryset(self):
        return Application.objects.filter(
            selected_mentor=self.request.user
        ).exclude(status='draft').select_related(
            'applicant', 'selected_availability_slot'
        ).order_by('-submitted_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = Application.objects.filter(selected_mentor=self.request.user).exclude(status='draft')
        context['pending_count'] = qs.filter(status='pending_review').count()
        context['approved_count'] = qs.filter(status__in=['approved', 'enrolled']).count()
        context['rejected_count'] = qs.filter(status__in=['finance_rejected', 'review_rejected']).count()
        return context


class MentorApplicationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Mentor views single mentorship application"""
    model = Application
    template_name = 'applications/mentor_application_detail.html'
    context_object_name = 'application'

    def test_func(self):
        app = self.get_object()
        return app.selected_mentor == self.request.user

    def get_queryset(self):
        return Application.objects.select_related(
            'applicant', 'selected_mentor', 'selected_availability_slot'
        )


# ==================== PAY AND SUBMIT APPLICATION (logged-in student) ====================

@login_required
def pay_and_submit_application(request, request_id):
    """
    Student pays application fee to submit their mentorship request.
    Creates Application linked to MentorshipRequest; on payment submit -> status pending_finance.
    """
    from mentorship.models import MentorshipRequest
    from django.contrib.contenttypes.models import ContentType

    mentorship_request = get_object_or_404(
        MentorshipRequest,
        pk=request_id,
        student=request.user,
        status='pending'
    )

    # Get or create Application for this mentorship request
    application, created = Application.objects.get_or_create(
        mentorship_request=mentorship_request,
        defaults={
            'applicant': request.user,
            'name': request.user.get_full_name(),
            'email': request.user.email,
            'status': 'draft',
        }
    )
    if created:
        application.applicant = request.user
        application.name = request.user.get_full_name()
        application.email = request.user.email
        application.save()

    # If already submitted (has payment), redirect to request detail or applications list
    if application.status != 'draft':
        messages.info(request, 'This application has already been submitted.')
        return redirect('mentorship:request_detail', pk=request_id)

    from payments.models import PaymentSettings
    settings_obj = PaymentSettings.objects.order_by('-updated_at').first()
    application_fee = settings_obj.student_payment_amount if settings_obj else 0

    if request.method == 'POST':
        form = ApplicationPaymentForm(request.POST, request.FILES)
        if form.is_valid():
            transaction_code = form.cleaned_data['transaction_code'].strip()
            if Payment.objects.filter(transaction_code=transaction_code).exists():
                form.add_error('transaction_code', 'This transaction code has already been used.')
            else:
                payment = Payment.objects.create(
                    application=application,
                    amount=application_fee,
                    transaction_code=transaction_code,
                    receipt=form.cleaned_data.get('receipt') or None,
                )
                application.status = 'pending_finance'
                application.submitted_at = timezone.now()
                application.save(update_fields=['status', 'submitted_at'])

                # Log activity
                ct = ContentType.objects.get_for_model(Application)
                ActivityLog.objects.create(
                    content_type=ct,
                    object_id=application.id,
                    action_type='payment_submitted',
                    new_status='pending_finance',
                    details=f'Payment {payment.transaction_code} submitted.',
                    performed_by=request.user,
                )
                messages.success(
                    request,
                    'Your payment has been submitted. Finance will verify it shortly. You can check status in your applications.'
                )
                return redirect('mentorship:request_detail', pk=request_id)
    else:
        form = ApplicationPaymentForm()

    return render(request, 'applications/pay_and_submit.html', {
        'mentorship_request': mentorship_request,
        'application': application,
        'form': form,
        'application_fee': application_fee,
    })


# ==================== MULTI-STEP APPLICATION WIZARD ====================

def _get_wizard_session(request):
    """Get or create wizard session (for public or registered user)."""
    if request.user.is_authenticated and request.user.is_student:
        ws = ApplicationWizardSession.objects.filter(
            user=request.user,
            application__status='draft'
        ).select_related('application').order_by('-updated_at').first()
        if not ws:
            app = Application.objects.create(
                applicant=request.user,
                name=request.user.get_full_name(),
                email=request.user.email,
                status='draft',
            )
            ws = ApplicationWizardSession.objects.create(user=request.user, application=app, is_public=False)
        return ws
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        ws = ApplicationWizardSession.objects.filter(
            session_key=session_key,
            application__status='draft'
        ).select_related('application').order_by('-updated_at').first()
        if not ws:
            app = Application.objects.create(status='draft')
            ws = ApplicationWizardSession.objects.create(session_key=session_key, application=app, is_public=True)
        return ws


def application_wizard(request, step=None):
    """
    Multi-step mentorship application wizard.
    Supports both registered students and public applicants.
    """
    # Ensure session for public
    if not request.session.session_key:
        request.session.create()
    if request.user.is_authenticated and not request.user.is_student:
        messages.warning(request, 'Only students can apply. Please log in as a student or apply as a public applicant.')
        return redirect('core:home')
    ws = _get_wizard_session(request)
    app = ws.application
    current_step = int(step) if step else ws.current_step
    current_step = max(1, min(5, current_step))
    # Prevent skipping steps - redirect to highest completed step
    if current_step > app.current_step:
        current_step = app.current_step
        if step:
            return redirect('applications:wizard_step', step=current_step)
    from payments.models import PaymentSettings
    settings_obj = PaymentSettings.objects.order_by('-updated_at').first()
    application_fee = settings_obj.student_payment_amount if settings_obj else 0
    form = None
    slots_qs = None
    availability_by_date = None
    if request.method == 'POST':
        if current_step == 1:
            form = ApplicationWizardStep1Form(request.POST)
            if form.is_valid():
                app.name = form.cleaned_data['name']
                app.email = form.cleaned_data['email']
                app.phone = form.cleaned_data.get('phone', '')
                app.date_of_birth = form.cleaned_data.get('date_of_birth')
                app.parent_name = form.cleaned_data.get('parent_name', '')
                app.parent_email = form.cleaned_data.get('parent_email', '')
                app.parent_phone = form.cleaned_data.get('parent_phone', '')
                app.parent_relationship = form.cleaned_data.get('parent_relationship', '')
                app.parent_consent_given = form.cleaned_data.get('parent_consent_given', False)
                app.current_step = 2
                app.save()
                ws.current_step = 2
                ws.updated_at = timezone.now()
                ws.save(update_fields=['current_step', 'updated_at'])
                return redirect('applications:wizard_step', step=2)
        elif current_step == 2:
            form = ApplicationWizardStep2Form(request.POST)
            if form.is_valid():
                app.school = form.cleaned_data.get('school', '')
                app.program = form.cleaned_data.get('program', '')
                app.career_goals = form.cleaned_data.get('career_goals', '')
                app.motivation = form.cleaned_data.get('motivation', '')
                app.expectations = form.cleaned_data.get('expectations', '')
                app.current_step = 3
                app.save()
                ws.current_step = 3
                ws.save(update_fields=['current_step', 'updated_at'])
                return redirect('applications:wizard_step', step=3)
        elif current_step == 3:
            filter_only = 'filter_mentor' in request.POST
            form = ApplicationWizardStep3Form(request.POST, mentor_id=request.POST.get('mentor'))
            if filter_only:
                # This is just a filter request, don't validate or advance step
                # Clear any validation errors for availability_slot since it's not required for filtering
                if form.errors:
                    form.errors.pop('availability_slot', None)
            elif form.is_valid():
                app.selected_mentor = form.cleaned_data['mentor']
                app.selected_availability_slot = form.cleaned_data['availability_slot']
                app.current_step = 4
                app.save()
                ws.current_step = 4
                ws.save(update_fields=['current_step', 'updated_at'])
                return redirect('applications:wizard_step', step=4)
        elif current_step == 4:
            form = ApplicationPaymentForm(request.POST, request.FILES)
            if form.is_valid():
                tc = form.cleaned_data['transaction_code'].strip()
                if Payment.objects.filter(transaction_code=tc).exists():
                    form.add_error('transaction_code', 'This transaction code has already been used.')
                else:
                    Payment.objects.create(
                        application=app,
                        amount=application_fee,
                        transaction_code=tc,
                        receipt=form.cleaned_data.get('receipt'),
                    )
                    app.current_step = 5
                    app.save(update_fields=['current_step'])
                    ws.current_step = 5
                    ws.save(update_fields=['current_step', 'updated_at'])
                    return redirect('applications:wizard_step', step=5)
        elif current_step == 5:
            # Final submit
            app.status = 'pending_finance'
            app.submitted_at = timezone.now()
            app.save(update_fields=['status', 'submitted_at'])
            ct = ContentType.objects.get_for_model(Application)
            ActivityLog.objects.create(
                content_type=ct, object_id=app.id,
                action_type='payment_submitted',
                new_status='pending_finance',
                details='Application submitted.',
                performed_by=request.user if request.user.is_authenticated else None,
            )
            messages.success(
                request,
                f'Your application has been submitted! Tracking code: {app.tracking_code}. '
                'Save it to track your application. Finance will verify your payment shortly.'
            )
            if request.user.is_authenticated:
                return redirect('applications:my_applications')
            return redirect('applications:track_status')
    # Compute availability slots for step 3 if form is already created (POST with validation errors or filter)
    if current_step == 3 and form is not None:
        slots_qs = form.fields['availability_slot'].queryset
        availability_by_date = {}
        for slot in slots_qs:
            date_str = slot.date.isoformat()
            availability_by_date.setdefault(date_str, []).append(slot)
    if form is None:
        if current_step == 1:
            form = ApplicationWizardStep1Form(initial={
                'name': app.name or (request.user.get_full_name() if request.user.is_authenticated else ''),
                'email': app.email or (request.user.email if request.user.is_authenticated else ''),
                'phone': app.phone,
                'date_of_birth': app.date_of_birth,
                'parent_name': app.parent_name,
                'parent_email': app.parent_email,
                'parent_phone': app.parent_phone,
                'parent_relationship': app.parent_relationship,
                'parent_consent_given': app.parent_consent_given,
            })
        elif current_step == 2:
            form = ApplicationWizardStep2Form(initial={
                'school': app.school,
                'program': app.program,
                'career_goals': app.career_goals,
                'motivation': app.motivation,
                'expectations': app.expectations,
            })
        elif current_step == 3:
            mentor_id_val = app.selected_mentor_id or (request.POST.get('mentor') if request.method == 'POST' else None)
            if mentor_id_val and isinstance(mentor_id_val, str):
                try:
                    mentor_id_val = int(mentor_id_val)
                except (ValueError, TypeError):
                    mentor_id_val = None
            form = ApplicationWizardStep3Form(
                initial={
                    'mentor': app.selected_mentor_id,
                    'availability_slot': app.selected_availability_slot_id,
                },
                mentor_id=mentor_id_val
            )
            # Prepare availability slots for calendar display
            slots_qs = form.fields['availability_slot'].queryset
            # Group slots by date for template
            availability_by_date = {}
            for slot in slots_qs:
                date_str = slot.date.isoformat()
                availability_by_date.setdefault(date_str, []).append(slot)
        elif current_step == 4:
            form = ApplicationPaymentForm()
            slots_qs = None
            availability_by_date = None
        elif current_step == 5:
            form = None  # Review step, no form
            slots_qs = None
            availability_by_date = None
        else:
            slots_qs = None
            availability_by_date = None
    return render(request, 'applications/wizard_step.html', {
        'application': app,
        'wizard_session': ws,
        'step': current_step,
        'form': form,
        'application_fee': application_fee,
        'progress_percent': min(100, int((current_step / 5) * 100)),
        'availability_slots': slots_qs,
        'availability_by_date': availability_by_date,
    })


def get_mentor_availability_html(request):
    """Return HTML for availability slots of a given mentor (AJAX endpoint)."""
    from django.db.models import F
    from mentorship.models import MentorAvailability
    from django.utils import timezone
    from django.http import HttpResponseBadRequest

    mentor_id = request.GET.get('mentor_id')
    selected_slot_id = request.GET.get('selected_slot_id')
    if not mentor_id:
        return HttpResponseBadRequest('Missing mentor_id')

    today = timezone.now().date()
    slots_qs = MentorAvailability.objects.filter(
        mentor_id=mentor_id,
        date__gte=today
    ).filter(current_bookings__lt=F('max_bookings')).select_related('mentor').order_by('date', 'start_time')

    availability_by_date = {}
    for slot in slots_qs:
        date_str = slot.date.isoformat()
        availability_by_date.setdefault(date_str, []).append(slot)

    return render(request, 'applications/includes/availability_slots.html', {
        'availability_by_date': availability_by_date,
        'selected_slot_id': selected_slot_id,
    })


def application_track_status(request):
    """Public applicants track application by email + tracking code."""
    application = None
    if request.method == 'POST':
        form = ApplicationTrackingForm(request.POST)
        if form.is_valid():
            application = Application.objects.filter(
                email__iexact=form.cleaned_data['email'],
                tracking_code__iexact=form.cleaned_data['tracking_code'].strip()
            ).select_related('selected_mentor', 'selected_availability_slot').first()
            if not application:
                form.add_error(None, 'No application found with that email and tracking code.')
    else:
        form = ApplicationTrackingForm()
    return render(request, 'applications/track_status.html', {
        'form': form,
        'application': application,
    })


class StudentApplicationsListView(LoginRequiredMixin, ListView):
    """Registered students view their applications."""
    template_name = 'applications/my_applications.html'
    context_object_name = 'applications'
    paginate_by = 10

    def get_queryset(self):
        return Application.objects.filter(applicant=self.request.user).exclude(
            status='draft'
        ).select_related('selected_mentor', 'selected_availability_slot').order_by('-updated_at')
