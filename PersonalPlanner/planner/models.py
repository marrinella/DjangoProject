from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Event(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)

    date = models.DateField()
    time = models.TimeField()

    location = models.CharField(max_length=255, blank=True)

    is_notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # reminded_5min = models.BooleanField(default=False)
    reminded_5min_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} — {self.date} {self.time}"

class TelegramProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telegram_id = models.BigIntegerField(null=True, blank=True)
    link_code = models.CharField(max_length=20, blank=True, null=True)
    code_created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.telegram_id}"


