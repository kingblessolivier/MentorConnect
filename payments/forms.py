from django import forms
from .models import PaymentSettings, PaymentProof, Subscription


class PaymentAmountForm(forms.ModelForm):
    class Meta:
        model = PaymentSettings
        fields = ['student_payment_amount', 'application_fee', 'subscription_fee']
        widgets = {
            'student_payment_amount': forms.NumberInput(attrs={
                'class': 'form-input w-full px-4 py-3 rounded-lg border border-gray-300',
                'min': 0,
                'step': 0.01,
                'placeholder': 'Enter amount to be paid by students',
            }),
            'application_fee': forms.NumberInput(attrs={
                'class': 'form-input w-full px-4 py-3 rounded-lg border border-gray-300',
                'min': 0,
                'step': 0.01,
                'placeholder': 'Enter application fee amount',
            }),
            'subscription_fee': forms.NumberInput(attrs={
                'class': 'form-input w-full px-4 py-3 rounded-lg border border-gray-300',
                'min': 0,
                'step': 0.01,
                'placeholder': 'Enter monthly subscription fee',
            }),
        }


class PaymentProofForm(forms.ModelForm):
    """Form for students to upload payment proof."""
    payment_type = forms.ChoiceField(
        choices=[
            ('subscription', 'Subscription'),
            ('application', 'Application Fee'),
            ('other', 'Other'),
            ('momo', 'MTN MoMo'),
            ('card', 'Credit/Debit Card'),
            ('bank', 'Bank Transfer'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-input w-full px-4 py-3 rounded-lg border border-gray-300',
        })
    )
    class Meta:
        model = PaymentProof
        fields = ['payment_type', 'amount', 'proof_image']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-input w-full px-4 py-3 rounded-lg border border-gray-300',
                'min': 0,
                'step': 0.01,
                'placeholder': 'Amount paid',
            }),
            'proof_image': forms.FileInput(attrs={
                'class': 'form-input w-full px-4 py-3 rounded-lg border border-gray-300',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx',
            }),
        }


class PaymentProofReviewForm(forms.ModelForm):
    """Form for finance officer to approve/reject payment proof."""
    class Meta:
        model = PaymentProof
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-input w-full px-4 py-3 rounded-lg border border-gray-300',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-input w-full px-4 py-3 rounded-lg border border-gray-300',
                'rows': 3,
                'placeholder': 'Optional notes for the student',
            }),
        }


class SubscriptionForm(forms.ModelForm):
    """Form for creating/updating subscription (admin)."""
    class Meta:
        model = Subscription
        fields = ['user', 'plan', 'status', 'start_date', 'end_date', 'payment_proof']
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-input w-full px-4 py-3 rounded-lg border border-gray-300',
            }),
            'plan': forms.Select(attrs={
                'class': 'form-input w-full px-4 py-3 rounded-lg border border-gray-300',
            }),
            'status': forms.Select(attrs={
                'class': 'form-input w-full px-4 py-3 rounded-lg border border-gray-300',
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-input w-full px-4 py-3 rounded-lg border border-gray-300',
                'type': 'date',
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-input w-full px-4 py-3 rounded-lg border border-gray-300',
                'type': 'date',
            }),
            'payment_proof': forms.Select(attrs={
                'class': 'form-input w-full px-4 py-3 rounded-lg border border-gray-300',
            }),
        }
