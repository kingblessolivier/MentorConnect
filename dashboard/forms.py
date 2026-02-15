from django import forms
from core.models import SiteSettings
from .models import ContactMessage

class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'site_name', 'site_tagline', 'site_logo', 'site_favicon',
            'contact_email', 'contact_phone', 'contact_address',
            'facebook_url', 'twitter_url', 'linkedin_url', 'instagram_url',
            'footer_text', 'enable_chat', 'enable_feed', 'enable_notifications',
            'enable_text_to_speech', 'maintenance_mode', 'maintenance_message'
        ]
        widgets = {
            'site_name': forms.TextInput(attrs={'class': 'form-control'}),
            'site_tagline': forms.TextInput(attrs={'class': 'form-control'}),
            'site_logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'site_favicon': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_address': forms.Textarea(attrs={'class': 'form-control form-textarea', 'rows': 3}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control'}),
            'footer_text': forms.Textarea(attrs={'class': 'form-control form-textarea', 'rows': 2}),
            'maintenance_message': forms.Textarea(attrs={'class': 'form-control form-textarea', 'rows': 2}),
            'enable_chat': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_feed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_text_to_speech': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'maintenance_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your full name',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'your.email@example.com',
                'required': True
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'What is this regarding?',
                'required': True
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 5,
                'placeholder': 'Please provide details about your inquiry...',
                'required': True
            }),
        }
    
    def clean_message(self):
        message = self.cleaned_data.get('message', '')
        if len(message.strip()) < 10:
            raise forms.ValidationError('Please provide a more detailed message (at least 10 characters).')
        return message
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError('Please enter your full name.')
        return name
