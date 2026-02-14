"""
Payments App Models
Invoices for applications, mentor earnings, and payouts
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


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
