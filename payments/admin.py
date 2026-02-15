from django.contrib import admin
from .models import Invoice, MentorEarning, Payout, PaymentSettings, PaymentProof, Subscription


@admin.register(PaymentSettings)
class PaymentSettingsAdmin(admin.ModelAdmin):
    list_display = ('student_payment_amount', 'application_fee', 'subscription_fee', 'updated_at')


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


@admin.register(PaymentProof)
class PaymentProofAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'payment_type', 'amount', 'status', 'submitted_at', 'reviewed_by', 'reviewed_at')
    list_filter = ('status', 'payment_type')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('submitted_at',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'status', 'start_date', 'end_date', 'is_active', 'created_at')
    list_filter = ('status', 'plan')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    
    def is_active(self, obj):
        return obj.is_active()
    is_active.boolean = True
    
