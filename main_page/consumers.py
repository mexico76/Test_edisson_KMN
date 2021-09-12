import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import DenyConnection
from django.contrib.auth.models import AnonymousUser

from .services import WaitingRoom, PlayerGame, Game, serialize_and_put_to_cache, deserialize_and_get_from_cache


class WaitingRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.player = PlayerGame(self.scope['user'])
        self.waiting_room = WaitingRoom()
        self.room_group_name = 'waiting_room'
        await self.player.change_busy_status(False)
        # Join room group
        if self.player.username == AnonymousUser():
            raise DenyConnection("User is not exist")
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.player.change_online_status(True)
        user_list = await self.waiting_room.get_user_list_online()
        await self.receive({'user_list': user_list})
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        if type(text_data) == str:
            text_data = json.loads(text_data)
        message_dict = {}
        message_dict = await self.waiting_room.invite_logic(text_data, message_dict)
        user_list = await self.waiting_room.get_user_list_online()
        message_dict['user_list'] = user_list
        await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'group_message',
                    'message': message_dict
                }
            )

    # Receive message from room group
    async def group_message(self, event):
        message = event['message']
        # Send message to WebSocket
        await self.send(text_data=json.dumps(
            {'message': message}
        ))

    async def disconnect(self, close_code):
        # Leave room group
        await self.player.change_online_status(False)
        user_list = await self.waiting_room.get_user_list_online()
        await self.receive({'user_list': user_list})
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

class GameConsumer(AsyncWebsocketConsumer):
    '''Consumer for gaming'''
    async def connect(self):
        self.player = PlayerGame(self.scope['user'])
        self.user_names_key = str(self.scope['url_route']['kwargs']['user1'] + '-' + self.scope['url_route']['kwargs']['user2'])
        self.new_game = Game(self.scope['url_route']['kwargs']['user1'], self.scope['url_route']['kwargs']['user2'])
        await serialize_and_put_to_cache(self.user_names_key, self.new_game)
        self.room_group_name = f'game-{self.new_game.player1.username}-{self.new_game.player2.username}'
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        disconnect_info = await self.new_game.if_user_disconnect(self.scope['user'])
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_message',
                'message': disconnect_info
            }
        )
        await self.player.change_busy_status(False)
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        if type(text_data) == str:
            text_data = json.loads(text_data)
        user = text_data['user'] # curent user
        choice = text_data['choice']
        self.new_game = await deserialize_and_get_from_cache(self.user_names_key)
        await self.new_game.add_user_choice(user, choice)
        message = await self.new_game.check_if_user_make_choice_or_win_round_or_win_game(user)
        await serialize_and_put_to_cache(self.user_names_key, self.new_game)
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_message',
                'message': message
            }
        )

    # Receive message from room group
    async def game_message(self, event):
        message = event['message']
        # Send message to WebSocket
        await self.send(text_data=json.dumps(
            {'message': message}
        ))


