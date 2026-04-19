from django.contrib import admin
from .models import *
# Register your models here.


admin.site.register(UserProfile)
admin.site.register(JobPosting)
admin.site.register(Contract)
admin.site.register(EscrowPayment)
admin.site.register(Notification)
admin.site.register(Complaint)
admin.site.register(SupportTicket)