from django.db import models
from case.models import Case
from users.models import CustomUser as User

class PremiumChatMessage(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    room = models.ForeignKey(Case, on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f'[{self.timestamp}] {self.user}: {self.content}'