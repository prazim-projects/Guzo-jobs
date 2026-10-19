from django.contrib import admin
from .models import *
# Register your models here.


admin.site.register(UserProfile)
admin.site.register(JobPosting)
admin.site.register(Contract)
@admin.register(EscrowRecipient)
class EscrowRecipientAdmin(admin.ModelAdmin):
    list_display = ('provider', 'name', 'account_number', 'is_active', 'updated_at')
    readonly_fields = ('updated_at',)


@admin.register(EscrowPayment)
class EscrowPaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'contract', 'payment_method', 'amount', 'status', 'tx_ref', 'verified_at')
    readonly_fields = tuple(field.name for field in EscrowPayment._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
admin.site.register(Notification)
admin.site.register(Complaint)
admin.site.register(SupportTicket)
