from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Case
from .serializers import CaseSerializer

class CaseListCreateView(generics.ListCreateAPIView):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    permission_classes = [IsAuthenticated]

class CaseRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    permission_classes = [IsAuthenticated]