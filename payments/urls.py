from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('set-amount/', views.set_payment_amount, name='set_payment_amount'),
    path('payment-proofs/', views.PaymentProofListView.as_view(), name='paymentproof_list'),
]
