from django.urls import path
from .views import ChatCreateView, ChatListView

urlpatterns = [
    path('', ChatListView.as_view(), name='chat_rooms'),
    path('create-chat-room/', ChatCreateView.as_view(), name='create_chat_room'),
]
