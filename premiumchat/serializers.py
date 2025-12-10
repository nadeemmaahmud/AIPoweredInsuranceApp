from rest_framework import serializers
from .models import PremiumMessage
from case.models import Case

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PremiumMessage
        fields = ['id', 'room', 'sender', 'content', 'timestamp']
        read_only_fields = ['timestamp', 'id', 'sender', 'room']

class CaseSerializer(serializers.ModelSerializer):
    premium_messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Case
        fields = ['id', 'type_of_injury', 'description', 'premium_messages']
        read_only_fields = ['id']