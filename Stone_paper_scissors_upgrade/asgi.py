"""
ASGI config for Stone_paper_scissors_upgrade project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""
import os
import django

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import main_page.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Stone_paper_scissors_upgrade.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            main_page.routing.websocket_urlpatterns
        )
    ),
})

