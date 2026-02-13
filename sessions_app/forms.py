from django import forms
from .models import Availability, Session
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability
        fields = ['start', 'end', 'session_type', 'location_name', 'address', 'latitude', 'longitude', 'is_active']
        widgets = {
            'start': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
            'end': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
            'location_name': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start')
        end = cleaned.get('end')
        if start and end and end <= start:
            self.add_error('end', 'End must be after start.')
        return cleaned


class SessionRequestForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }


class SessionCreateForm(forms.ModelForm):
    student = forms.ModelChoiceField(queryset=User.objects.all(), required=True, label='Student')

    class Meta:
        model = Session
        fields = ['student', 'title', 'description', 'start', 'end', 'session_type', 'location_name', 'address']
        widgets = {
            'start': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
            'end': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
            'location_name': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start')
        end = cleaned.get('end')
        if start and end and end <= start:
            self.add_error('end', 'End must be after start.')
        return cleaned
