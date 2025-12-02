from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ChatRoomSerializer
from .models import ChatRoom
from rest_framework.permissions import IsAuthenticated

class ChatCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatRoomSerializer(data=request.data)
        if serializer.is_valid():
            chat_room = serializer.save(commit=False)
            chat_room.name = f"chat_room_{chat_room.messasges.count()+1}" 
            serializer = ChatRoomSerializer(chat_room)
            return Response({"message": "Chat room created successfully","chat_room": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ChatListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        chat_rooms = ChatRoom.objects.all()
        serializer = ChatRoomSerializer(chat_rooms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)