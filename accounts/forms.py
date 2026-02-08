"""
Accounts App Forms
Beautiful, modern forms for authentication
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class BaseFormMixin:
    """
    Mixin to add modern styling to form fields
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Add common CSS classes
            css_classes = 'form-input w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-primary focus:ring-2 focus:ring-primary focus:ring-opacity-20 transition-all duration-200'

            if isinstance(field.widget, forms.CheckboxInput):
                css_classes = 'form-checkbox h-5 w-5 text-primary rounded border-gray-300 focus:ring-primary'
            elif isinstance(field.widget, forms.Select):
                css_classes = 'form-select w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-primary focus:ring-2 focus:ring-primary focus:ring-opacity-20 transition-all duration-200'
            elif isinstance(field.widget, forms.Textarea):
                css_classes = 'form-textarea w-full px-4 py-3 rounded-lg border border-gray-300 focus:border-primary focus:ring-2 focus:ring-primary focus:ring-opacity-20 transition-all duration-200 resize-none'
            elif isinstance(field.widget, forms.FileInput):
                css_classes = 'form-input file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-primary file:text-white hover:file:bg-primary-hover cursor-pointer w-full'

            field.widget.attrs.update({
                'class': css_classes,
                'placeholder': field.label or field_name.replace('_', ' ').title(),
            })


class LoginForm(BaseFormMixin, AuthenticationForm):
    """
    Modern login form
    """
    username = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'autocomplete': 'email',
            'aria-label': 'Email address',
        })
    )
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'aria-label': 'Password',
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        label=_('Remember me'),
        widget=forms.CheckboxInput()
    )

    error_messages = {
        'invalid_login': _('Please enter a correct email and password.'),
        'inactive': _('This account is inactive.'),
    }


class StudentRegistrationForm(BaseFormMixin, UserCreationForm):
    """
    Registration form for students
    """
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'aria-label': 'Email address',
        })
    )
    first_name = forms.CharField(
        label=_('First Name'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'autocomplete': 'given-name',
            'aria-label': 'First name',
        })
    )
    last_name = forms.CharField(
        label=_('Last Name'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'autocomplete': 'family-name',
            'aria-label': 'Last name',
        })
    )
    terms = forms.BooleanField(
        required=True,
        label=_('I agree to the Terms of Service and Privacy Policy')
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('An account with this email already exists.'))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.STUDENT
        if commit:
            user.save()
        return user


class MentorRegistrationForm(BaseFormMixin, UserCreationForm):
    """
    Registration form for mentors
    """
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'aria-label': 'Email address',
        })
    )
    first_name = forms.CharField(
        label=_('First Name'),
        max_length=100
    )
    last_name = forms.CharField(
        label=_('Last Name'),
        max_length=100
    )
    phone = forms.CharField(
        label=_('Phone Number'),
        max_length=20,
        required=False
    )
    expertise = forms.CharField(
        label=_('Area of Expertise'),
        max_length=200,
        help_text=_('e.g., Software Engineering, Data Science, Business')
    )
    experience_years = forms.IntegerField(
        label=_('Years of Experience'),
        min_value=0,
        max_value=50
    )
    city = forms.CharField(
        label=_('City/Region'),
        max_length=100,
        required=False,
        help_text=_('Where students can shadow you')
    )
    terms = forms.BooleanField(
        required=True,
        label=_('I agree to the Terms of Service, Privacy Policy, and Mentor Guidelines')
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('An account with this email already exists.'))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.MENTOR
        if commit:
            user.save()
            # Save expertise, experience_years, and city to MentorProfile
            try:
                from profiles.models import MentorProfile
                mentor_data = {
                    'expertise': self.cleaned_data.get('expertise', ''),
                    'experience_years': self.cleaned_data.get('experience_years', 0),
                }
                # Add city if the field exists in MentorProfile
                if self.cleaned_data.get('city'):
                    mentor_data['city'] = self.cleaned_data.get('city', '')

                MentorProfile.objects.get_or_create(
                    user=user,
                    defaults=mentor_data
                )
            except Exception:
                pass
        return user


class UserUpdateForm(BaseFormMixin, forms.ModelForm):
    """
    Form for updating user profile
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'avatar', 'language']
        widgets = {
            'avatar': forms.FileInput(attrs={
                'accept': 'image/*',
                'aria-label': 'Profile photo',
            }),
        }


class CustomPasswordResetForm(BaseFormMixin, PasswordResetForm):
    """
    Modern password reset form
    """
    email = forms.EmailField(
        label=_('Email'),
        max_length=254,
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'aria-label': 'Email address',
        })
    )
