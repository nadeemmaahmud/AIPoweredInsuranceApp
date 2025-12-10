import os
import requests
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import PremiumMessage
from case.models import Case
from .serializers import CaseSerializer, MessageSerializer
from django.conf import settings

MODEL_NAME = "llama-3.1-8b-instant"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = settings.GROQ_API_KEY

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json",
}

class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = CaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Case.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def send_message(self, request, pk=None):
        chatroom = self.get_object()
        user_text = request.data.get("message", "").strip()

        if not user_text:
            return Response({"error": "Message text is required"}, status=400)

        user_msg = PremiumMessage.objects.create(
            room=chatroom,
            sender="user",
            content=user_text
        )

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_text}
            ]
        }

        try:
            resp = requests.post(GROQ_API_URL, headers=HEADERS, json=payload)
        except Exception as e:
            return Response(
                {"error": "Failed to connect to Groq API", "details": str(e)},
                status=500
            )

        if resp.status_code != 200:
            return Response(
                {
                    "error": "Groq API returned an error",
                    "status": resp.status_code,
                    "details": resp.text
                },
                status=resp.status_code
            )

        data = resp.json()

        try:
            ai_text = data["choices"][0]["message"]["content"]
        except Exception:
            return Response(
                {"error": "Invalid AI response format", "data": data},
                status=500
            )

        ai_msg = PremiumMessage.objects.create(
            room=chatroom,
            sender="ai",
            content=ai_text
        )

        return Response(
            {
                "user_message": MessageSerializer(user_msg).data,
                "ai_message": MessageSerializer(ai_msg).data
            },
            status=200
        )