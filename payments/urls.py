from django.urls import path
from .views import IAPVerifyView

urlpatterns = [
    path('iap/verify/', IAPVerifyView.as_view()),
]
