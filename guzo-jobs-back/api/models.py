from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class UserProfile(AbstractUser):
    bio = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, unique=True)

class JobPosting(models.Model):
    class PostType(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Customer'
        COURIER = 'COURIER', 'Courier'

    title = models.CharField(max_length=255)
    description = models.TextField()
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='job_postings')
    expires_at = models.DateTimeField()
    origin = models.CharField(max_length=255, blank=True, null=True)
    destination = models.CharField(max_length=255, blank=True, null=True)
    post_type = models.CharField(max_length=10, choices=PostType.choices, default=PostType.CUSTOMER)