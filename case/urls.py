from django.urls import path
from .views import (
    CaseListView, CaseDetailView,
    CaseCreateView, CaseUpdateView,
    CaseDeleteView
)

urlpatterns = [
    path('', CaseListView.as_view(), name='case-list'),
    path('<int:pk>/', CaseDetailView.as_view(), name='case-detail'),
    path('create/', CaseCreateView.as_view(), name='case-create'),
    path('<int:pk>/update/', CaseUpdateView.as_view(), name='case-update'),
    path('<int:pk>/delete/', CaseDeleteView.as_view(), name='case-delete'),
]
