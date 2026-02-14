from django.contrib import admin
from .models import Invoice, MentorEarning, Payout


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'application', 'student', 'mentor', 'amount', 'payment_status', 'due_date', 'created_at')
    list_filter = ('payment_status',)
    search_fields = ('application__tracking_code', 'payment_reference')


@admin.register(MentorEarning)
class MentorEarningAdmin(admin.ModelAdmin):
    list_display = ('id', 'mentor', 'invoice', 'gross_amount', 'commission', 'net_payout', 'paid', 'paid_at')
    list_filter = ('paid',)


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'mentor', 'amount', 'payout_date', 'is_paid', 'reference', 'created_at')
    list_filter = ('is_paid',)
