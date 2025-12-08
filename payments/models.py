from django.db import models
from users.models import CustomUser as User

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    platform = models.CharField(max_length=10)
    product_id = models.CharField(max_length=100)
    purchase_token = models.TextField()
    expiry = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)
