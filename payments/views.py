"""
Payments App Views
Payment submission (student), verification (finance), and payouts
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import PaymentSettings
from .forms import PaymentAmountForm

# Placeholder for payment-related views (e.g. submit payment, verify, list)
# Main flow is in applications/views (submit with payment) and dashboard (finance verify)

# Utility to check if user is finance officer
def is_finance_officer(user):
	return user.is_authenticated and getattr(user, 'role', None) == 'finance_officer'

# View for finance officer to set payment amount
@user_passes_test(is_finance_officer)
def set_payment_amount(request):
	latest_settings = PaymentSettings.objects.order_by('-updated_at').first()
	if request.method == 'POST':
		form = PaymentAmountForm(request.POST, instance=latest_settings)
		if form.is_valid():
			form.save()
			return redirect('set_payment_amount')
	else:
		form = PaymentAmountForm(instance=latest_settings)
	return render(request, 'payments/set_payment_amount.html', {'form': form, 'current_amount': latest_settings.student_payment_amount if latest_settings else 0})


class PaymentProofListView(LoginRequiredMixin, ListView):
    """List payment proofs for the current user"""
    template_name = 'payments/paymentproof_list.html'
    context_object_name = 'payment_proofs'
    paginate_by = 20

    def get_queryset(self):
        from .models import PaymentProof
        return PaymentProof.objects.filter(user=self.request.user).order_by('-submitted_at')
