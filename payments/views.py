from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import IAPVerifySerializer
from .utils import verify_android_purchase#, verify_ios_purchase

class IAPVerifyView(APIView):
    def post(self, request):
        serializer = IAPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        platform = serializer.validated_data["platform"]
        token = serializer.validated_data["purchase_token"]
        product = serializer.validated_data["product_id"]

        if platform == "android":
            result = verify_android_purchase(token, product)
        #else:
        #    result = verify_ios_purchase(token, product)

        if not result["valid"]:
            return Response({"detail": "Invalid purchase"}, status=400)

        user = request.user
        user.subscription_active = True
        user.subscription_expiry = result.get("expiry")
        user.save()

        return Response({"status": "success", "expiry": result.get("expiry")})