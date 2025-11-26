from django.urls import path
from .views import CaseListCreateView, CaseRetrieveUpdateDeleteView

urlpatterns = [
    path('', CaseListCreateView.as_view(), name='case-list-create'),
    path('<int:pk>/', CaseRetrieveUpdateDeleteView.as_view(), name='case-detail'),
]