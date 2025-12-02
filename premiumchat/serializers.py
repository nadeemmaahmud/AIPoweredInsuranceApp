from rest_framework import serializers
from generalchat.models import ChatRoom, Message

class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['created_at', 'id']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'room', 'user', 'content', 'timestamp']
        read_only_fields = ['timestamp', 'id', 'user', 'room']