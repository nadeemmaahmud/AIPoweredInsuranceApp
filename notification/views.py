# notifications/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Device

class RegisterDeviceView(APIView):
    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"error": "Token required"}, status=status.HTTP_400_BAD_REQUEST)
        
        device, created = Device.objects.get_or_create(user=request.user, registration_id=token)
        return Response({"success": True, "created": created})

