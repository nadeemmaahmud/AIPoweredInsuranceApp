from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Case, CaseFile
from .serializers import CaseSerializer, CaseCreateUpdateSerializer
from rest_framework.permissions import IsAuthenticated

class CaseListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cases = Case.objects.filter(user=request.user)
        serializer = CaseSerializer(cases, many=True)
        return Response({"cases": serializer.data}, status=status.HTTP_200_OK)

class CaseDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            case = Case.objects.get(pk=pk, user=request.user)
        except Case.DoesNotExist:
            return Response({'detail': 'Case not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CaseSerializer(case)
        return Response({"case": serializer.data}, status=status.HTTP_200_OK)

class CaseCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CaseCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            case = serializer.save(user=request.user)
            serializer = CaseSerializer(case)
            return Response({"case": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CaseUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            case = Case.objects.get(pk=pk, user=request.user)
        except Case.DoesNotExist:
            return Response({'detail': 'Case not found'}, status=status.HTTP_404_NOT_FOUND)

        delete_file_ids = request.data.get('delete_file_ids', [])
        if delete_file_ids:
            CaseFile.objects.filter(id__in=delete_file_ids, case=case).delete()

        serializer = CaseCreateUpdateSerializer(case, data=request.data, partial=True)
        if serializer.is_valid():
            case = serializer.save()
            serializer = CaseSerializer(case)
            return Response({"case": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CaseDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            case = Case.objects.get(pk=pk, user=request.user)
        except Case.DoesNotExist:
            return Response({'detail': 'Case not found'}, status=status.HTTP_404_NOT_FOUND)
        case.delete()
        return Response({'detail': 'Case deleted'}, status=status.HTTP_204_NO_CONTENT)
