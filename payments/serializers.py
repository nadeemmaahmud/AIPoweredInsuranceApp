from rest_framework import serializers

class IAPVerifySerializer(serializers.Serializer):
    platform = serializers.ChoiceField(choices=["android", "ios"])
    purchase_token = serializers.CharField()
    product_id = serializers.CharField()
