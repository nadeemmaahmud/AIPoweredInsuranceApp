from django.db import models
from users.models import CustomUser as User
from case.models import Case

class PremiumMessage(models.Model):
    room = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="premium_messages")
    sender = models.CharField(max_length=50)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)