from django.db import models
from users.models import CustomUser as User

class ChatRoom(models.Model):
    name = models.CharField(max_length=255, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_private = models.BooleanField(default=True)
    participants = models.ForeignKey(User, blank=True, on_delete=models.CASCADE, null=True, related_name='chat_rooms')

    def __str__(self):
        return f"{self.name[:40]}" or f"Room {self.id}"

class Message(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f'[{self.timestamp}] {self.user}: {self.content}'

    def save(self, *args, **kwargs):
        if not self.pk:
            pass
        
        if not self.room and self.room_name:
            room, created = ChatRoom.objects.get_or_create(
                name=self.room_name,
                defaults={'display_name': self.room_name.title()}
            )
            self.room = room
        super().save(*args, **kwargs)