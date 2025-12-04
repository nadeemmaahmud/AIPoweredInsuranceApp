import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from generalchat.middleware import JWTAuthMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ChatApp.settings')

django_asgi_app = get_asgi_application()

from generalchat.routing import websocket_urlpatterns as chat_patterns
from premiumchat.routing import websocket_urlpatterns as premium_chat_patterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(
            chat_patterns + premium_chat_patterns
        )
    ),
})