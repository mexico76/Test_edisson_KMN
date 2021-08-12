from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/waiting_room/$', consumers.WaitingRoomConsumer.as_asgi()),
    re_path(r'ws/game-(?P<user1>\w+)-(?P<user2>\w+)/$', consumers.GameConsumer.as_asgi()),
]