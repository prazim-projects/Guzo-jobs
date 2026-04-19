from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class UserProfile(AbstractUser):
    bio = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, unique=True)
    profile_picture = models.URLField(blank=True, null=True)

class JobPosting(models.Model):
    class PostType(models.TextChoices):
        DELIVERY = 'DELIVERY', 'Delivery'
        TRANSPORT = 'TRANSPORT', 'Transport'
        ODDJOB = 'ODDJOB', 'Odd-job'
        TRADE = 'TRADE', "Trade"

    title = models.CharField(max_length=255)
    description = models.TextField()
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='job_postings')
    expires_at = models.DateTimeField()
    origin = models.CharField(max_length=255, blank=True, null=True)
    destination = models.CharField(max_length=255, blank=True, null=True)
    product_image = models.TextField(blank=True, null=True)
    post_type = models.CharField(max_length=10, choices=PostType.choices, default=PostType.DELIVERY)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)


class Contract(models.Model):
    class PreferredPaymentMethod(models.TextChoices):
        CHAPA = 'CHAPA', 'Chapa (Local Banks)'
        TELEBIRR = 'TELEBIRR', 'Telebirr'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        COMPLETED_BY_ACCEPTOR = 'COMPLETED_BY_ACCEPTOR', 'Completed by Acceptor'
        COMPLETED_BY_POSTER = 'COMPLETED_BY_POSTER', 'Completed by Poster'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    job_post = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='contract')
    poster = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='contracts_as_poster')
    acceptor = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='contracts_as_acceptor')
    status = models.CharField(max_length=21, choices=Status.choices, default=Status.PENDING)
    agreed_price = models.DecimalField(max_digits=10, decimal_places=2)
    preferred_payment_method = models.CharField(
        max_length=10,
        choices=PreferredPaymentMethod.choices,
        default=PreferredPaymentMethod.CHAPA,
    )
    preferred_chapa_bank = models.CharField(max_length=80, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Contract for {self.job_post.title} - {self.status} - {self.id}"


class EscrowPayment(models.Model):
    class Status(models.TextChoices):
        INITIATED = 'INITIATED', 'Initiated'
        PAID = 'PAID', 'Paid'
        RELEASED = 'RELEASED', 'Released'
        REFUNDED = 'REFUNDED', 'Refunded'

    class Method(models.TextChoices):
        CHAPA = 'CHAPA', 'Chapa'
        TELEBIRR = 'TELEBIRR', 'Telebirr'

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='escrow_payments')
    payer = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='escrow_payments_made')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=Method.choices)
    tx_ref = models.CharField(max_length=120)
    receipt_url = models.URLField(blank=True, null=True)
    verification_note = models.TextField(blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.INITIATED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Escrow({self.payment_method}) {self.status} for contract {self.contract_id}"


class Notification(models.Model):
    class Type(models.TextChoices):
        JOB_ACCEPTED = 'JOB_ACCEPTED', 'Job accepted'
        ESCROW_PAID = 'ESCROW_PAID', 'Escrow paid'
        JOB_COMPLETED = 'JOB_COMPLETED', 'Job completed'
        COMPLAINT_OPENED = 'COMPLAINT_OPENED', 'Complaint opened'
        SUPPORT_REPLY = 'SUPPORT_REPLY', 'Support reply'

    recipient = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications_sent')
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    type = models.CharField(max_length=20, choices=Type.choices)
    title = models.CharField(max_length=120)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification({self.type}) to {self.recipient.username}"


class Complaint(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under review'
        RESOLVED = 'RESOLVED', 'Resolved'
        REJECTED = 'REJECTED', 'Rejected'

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='complaints')
    filed_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='complaints_filed')
    against = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints_received')
    reason = models.TextField()
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Complaint {self.id} on contract {self.contract_id}"


class SupportTicket(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In progress'
        RESOLVED = 'RESOLVED', 'Resolved'

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='support_tickets')
    contract = models.OneToOneField(Contract, on_delete=models.SET_NULL, null=True, blank=True, related_name='support_ticket')
    subject = models.CharField(max_length=150)
    message = models.TextField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"SupportTicket {self.id} ({self.status})"