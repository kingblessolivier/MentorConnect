"""
Applications App Forms
Multi-step mentorship application forms
"""

from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class ApplicationPaymentForm(forms.Form):
    """Form for student to submit payment (transaction code + receipt) for application fee."""
    transaction_code = forms.CharField(
        max_length=64,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full px-4 py-3 rounded-lg border border-gray-300',
            'placeholder': 'e.g. MTN-1234567890 or BANK-REF-XXX',
        })
    )
    receipt = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-input file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-primary file:text-white',
            'accept': 'image/*,.pdf',
        })
    )

    def clean_transaction_code(self):
        import re
        code = self.cleaned_data.get('transaction_code', '').strip()
        if not re.match(r'^[A-Za-z0-9\-]+$', code):
            raise forms.ValidationError('Only letters, numbers and hyphens allowed.')
        return code


# ==================== Multi-step Application Wizard Forms ====================

class ApplicationWizardStep1Form(forms.Form):
    """Step 1: Personal Information"""
    name = forms.CharField(max_length=200, required=True, label='Full Name')
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=30, required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    parent_name = forms.CharField(max_length=200, required=False, label='Parent/Guardian Name')
    parent_email = forms.EmailField(required=False, label='Parent/Guardian Email')
    parent_phone = forms.CharField(max_length=30, required=False, label='Parent/Guardian Phone')
    parent_relationship = forms.CharField(max_length=50, required=False, label='Relationship')
    parent_consent_given = forms.BooleanField(required=False, initial=False, label='Parent consent obtained')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    def clean(self):
        from datetime import date
        data = super().clean()
        dob = data.get('date_of_birth')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                for f in ['parent_name', 'parent_email', 'parent_phone', 'parent_consent_given']:
                    val = data.get(f)
                    if f == 'parent_consent_given':
                        if not val:
                            self.add_error('parent_consent_given', 'Parent consent is required for applicants under 18.')
                    elif not val:
                        self.add_error(f, 'Required for applicants under 18.')
        return data


class ApplicationWizardStep2Form(forms.Form):
    """Step 2: Academic & Mentorship Goals"""
    school = forms.CharField(max_length=200, required=False, label='School/University')
    program = forms.CharField(max_length=200, required=False, label='Program of Study')
    career_goals = forms.CharField(widget=forms.Textarea, required=False, label='Career Goals')
    motivation = forms.CharField(widget=forms.Textarea, required=True, label='Motivation for Mentorship')
    expectations = forms.CharField(widget=forms.Textarea, required=False, label='Expectations from Mentor')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class ApplicationWizardStep3Form(forms.Form):
    """Step 3: Mentor Selection"""
    mentor = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=True,
        label='Preferred Mentor'
    )
    availability_slot = forms.ModelChoiceField(
        queryset=None,
        required=True,
        label='Preferred Session',
        empty_label='-- Select a session --'
    )

    def __init__(self, *args, mentor_id=None, **kwargs):
        from django.db.models import F
        from mentorship.models import MentorAvailability
        from django.utils import timezone
        super().__init__(*args, **kwargs)
        qs = User.objects.filter(role='mentor', is_active=True).select_related('mentor_profile').order_by('first_name')
        self.fields['mentor'].queryset = qs
        today = timezone.now().date()
        slot_qs = MentorAvailability.objects.filter(
            date__gte=today
        ).filter(current_bookings__lt=F('max_bookings')).select_related('mentor').order_by('date', 'start_time')
        if mentor_id:
            slot_qs = slot_qs.filter(mentor_id=mentor_id)
        self.fields['availability_slot'].queryset = slot_qs
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    def clean(self):
        data = super().clean()
        mentor = data.get('mentor')
        slot = data.get('availability_slot')
        if mentor and slot and slot.mentor_id != mentor.id:
            self.add_error('availability_slot', 'This session does not belong to the selected mentor.')
        return data


class ApplicationTrackingForm(forms.Form):
    """Form for public applicants to track their application"""
    email = forms.EmailField(required=True)
    tracking_code = forms.CharField(max_length=32, required=True, label='Tracking Code')
