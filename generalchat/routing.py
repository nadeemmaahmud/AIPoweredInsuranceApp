from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/generalchat/$', consumers.ChatBotConsumer.as_asgi()),
]