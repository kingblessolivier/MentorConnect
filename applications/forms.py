"""
Applications App Forms
Guest application form and invitation registration
"""

from django import forms
from django.contrib.auth import get_user_model
from .models import GuestApplication

User = get_user_model()


class GuestApplicationForm(forms.ModelForm):
    """Form for guest students to apply (no account required)"""

    class Meta:
        model = GuestApplication
        fields = ['name', 'email', 'school', 'interests', 'message', 'cv', 'mentor']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-primary focus:ring-2 focus:ring-primary/20',
                'placeholder': 'Your full name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-primary focus:ring-2 focus:ring-primary/20',
                'placeholder': 'your@email.com',
            }),
            'school': forms.TextInput(attrs={
                'class': 'form-input w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-primary focus:ring-2 focus:ring-primary/20',
                'placeholder': 'Your school or institution',
            }),
            'interests': forms.Textarea(attrs={
                'class': 'form-textarea w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-primary focus:ring-2 focus:ring-primary/20',
                'placeholder': 'What topics or fields interest you?',
                'rows': 3,
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-textarea w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-primary focus:ring-2 focus:ring-primary/20',
                'placeholder': 'Tell the mentor why you want to learn from them...',
                'rows': 4,
            }),
            'mentor': forms.Select(attrs={
                'class': 'form-select w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-primary focus:ring-2 focus:ring-primary/20',
            }),
            'cv': forms.FileInput(attrs={
                'class': 'form-input file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-primary file:text-white',
                'accept': '.pdf,.doc,.docx',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mentor'].queryset = User.objects.filter(
            role='mentor',
            is_active=True
        ).select_related('mentor_profile').order_by('first_name')
        self.fields['cv'].required = False


class MentorApplicationActionForm(forms.Form):
    """Form for mentor to approve/reject with feedback"""
    action = forms.ChoiceField(
        choices=[('approve', 'Approve'), ('reject', 'Reject')],
        widget=forms.RadioSelect(attrs={'class': 'form-radio'})
    )
    feedback = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea w-full px-4 py-3 rounded-lg',
            'rows': 3,
            'placeholder': 'Add feedback for the applicant...',
        })
    )
