from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from generalchat.models import ChatRoom, Message
from .serializers import ChatRoomSerializer, MessageSerializer

class ChatRoomCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatRoomSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChatRoomListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        chat_rooms = ChatRoom.objects.filter(user=request.user)
        serializer = ChatRoomSerializer(chat_rooms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ChatRoomUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, room_id):
        try:
            chat_room = ChatRoom.objects.get(id=room_id, user=request.user)
        except ChatRoom.DoesNotExist:
            return Response({"error": "Chat room not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, room=chat_room)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ChatRoomDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, room_id):
        try:
            chat_room = ChatRoom.objects.get(id=room_id, user=request.user)
            chat_room.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ChatRoom.DoesNotExist:
            return Response({"error": "Chat room not found."}, status=status.HTTP_404_NOT_FOUND)
        
class MessageCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, room_id):
        try:
            chat_room = ChatRoom.objects.get(id=room_id, user=request.user)
        except ChatRoom.DoesNotExist:
            return Response({"error": "Chat room not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, room=chat_room)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class MessageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, room_id):
        try:
            chat_room = ChatRoom.objects.get(id=room_id, user=request.user)
        except ChatRoom.DoesNotExist:
            return Response({"error": "Chat room not found."}, status=status.HTTP_404_NOT_FOUND)

        messages = Message.objects.filter(room=chat_room)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class MessageDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, message_id):
        try:
            message = Message.objects.get(id=message_id, user=request.user)
            message.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Message.DoesNotExist:
            return Response({"error": "Message not found."}, status=status.HTTP_404_NOT_FOUND)