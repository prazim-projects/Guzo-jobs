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
    post_type = models.CharField(max_length=10, choices=PostType.choices, default=PostType.DELIVERY)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)


class Contract(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Contract for {self.job_post.title} - {self.status} - {self.id}"