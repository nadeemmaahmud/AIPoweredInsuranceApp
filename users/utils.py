from rest_framework.response import Response
from django.utils.timezone import now

class ResponseMixin:
    def success_response(self, message, data=None, status_code=200):
        return Response({
            "success": True,
            "statusCode": status_code,
            "message": message,
            "data": data or {},
            "timestamp": now().isoformat()
        }, status=status_code)

    def error_response(self, message, data=None, status_code=400):
        return Response({
            "success": False,
            "statusCode": status_code,
            "message": message,
            "errors": data or {},
            "timestamp": now().isoformat()
        }, status=status_code)