"""
Payments App Models
Invoices for applications, mentor earnings, and payouts
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class PaymentSettings(models.Model):
    student_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    application_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Application Fee')
    subscription_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Monthly Subscription Fee')
    payment_number = models.CharField(max_length=100, blank=True, default='', verbose_name='Payment Number',
                                      help_text='MoMo number or bank account number students pay to')
    payment_code = models.CharField(max_length=200, blank=True, default='', verbose_name='Payment Code',
                                    help_text='USSD code or merchant code e.g. *182*8*1*123456#')
    payment_instructions = models.TextField(blank=True, default='', verbose_name='Payment Instructions',
                                            help_text='Instructions shown to students during subscription')
    updated_at = models.DateTimeField(auto_now=True)
    
    # Bank Details
    bank_name = models.CharField(max_length=100, default='Bank of Kigali (BK)', verbose_name='Bank Name')
    account_number = models.CharField(max_length=100, default='00040-0065432-12', verbose_name='Account Number')
    account_name = models.CharField(max_length=100, default='MentorConnect Ltd', verbose_name='Account Name')
    mobile_money_number = models.CharField(max_length=100, default='*182*8*1*556644#', verbose_name='Mobile Money Code')

    def __str__(self):
        return f"Payment Settings (App: {self.application_fee}, Sub: {self.subscription_fee})"

class Invoice(models.Model):
    """Invoice linked to an application (e.g. after approval for billing)."""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]

    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mentor_invoices'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    due_date = models.DateField()
    payment_reference = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'

    def __str__(self):
        return f"Invoice #{self.id} - {self.application.tracking_code} ({self.payment_status})"


class MentorEarning(models.Model):
    """Earning record for a mentor from an invoice (gross, commission, net)."""
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='mentor_earnings'
    )
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='earnings'
    )
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2)
    net_payout = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mentor Earning'
        verbose_name_plural = 'Mentor Earnings'

    def __str__(self):
        return f"{self.mentor.get_full_name()} - {self.net_payout} ({'paid' if self.paid else 'pending'})"


class Payout(models.Model):
    """Payout to a mentor (batch or single)."""
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payouts'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payout_date = models.DateField(default=timezone.now)
    reference = models.CharField(max_length=64, blank=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payout'
        verbose_name_plural = 'Payouts'

    def __str__(self):
        return f"Payout #{self.id} - {self.mentor.get_full_name()} - {self.amount}"


class PaymentProof(models.Model):
    """Proof of payment uploaded by student for subscription or application fee."""
    PAYMENT_TYPE_CHOICES = [
        ('subscription', 'Subscription'),
        ('application', 'Application Fee'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payment_proofs'
    )
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='subscription')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    proof_image = models.FileField(upload_to='payment_proofs/', verbose_name='Proof Document', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_payment_proofs'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Payment Proof'
        verbose_name_plural = 'Payment Proofs'

    def __str__(self):
        return f"Payment Proof #{self.id} - {self.user.get_full_name()} - {self.get_status_display()}"


class Subscription(models.Model):
    """Student subscription for premium features."""
    PLAN_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('lifetime', 'Lifetime'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='monthly')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    payment_proof = models.ForeignKey(
        PaymentProof,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscriptions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'

    def __str__(self):
        return f"Subscription #{self.id} - {self.user.get_full_name()} - {self.get_plan_display()} ({self.get_status_display()})"

    def is_active(self):
        """Check if subscription is currently active."""
        if self.status != 'active':
            return False
        if self.end_date and timezone.now().date() > self.end_date:
            return False
        return True
