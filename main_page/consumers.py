import json
import jsons
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import DenyConnection
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from asgiref.sync import async_to_sync


from .services import WaitingRoom, PlayerGame, Game, create_game, serialize_and_put_to_cache, \
    deserialize_and_get_from_cache


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
        if not cache.get(self.user_names_key):
            self.new_game = Game(self.scope['url_route']['kwargs']['user1'], self.scope['url_route']['kwargs']['user2'])
            await serialize_and_put_to_cache(self.user_names_key, self.new_game)
        else:
            self.new_game = await deserialize_and_get_from_cache(self.user_names_key, Game)
        print(self.new_game)
        '''Необходимо при коннекте первого пользователя создавать экземпляр Game, а следующий только будет к нему
         обращаться. Либо проверять создан ли экземпляр в кэше и если нет то создавать его и записывать в кэш'''
        # self.new_game = Game(self.scope['url_route']['kwargs']['user1'], self.scope['url_route']['kwargs']['user2'])
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
        await self.new_game.add_user_choice(user, choice)
        if not self.new_game.winner_data and len(self.new_game.player1.choices) == len(self.new_game.player2.choices):
            '''both users make choice'''
            if self.new_game.player1.choices[-1] == self.new_game.player2.choices[-1]:
                '''no one winner'''
            elif (self.new_game.player1.choices[-1] != self.new_game.player2.choices[-1]) and \
                (self.new_game.player2.choices[-1] in self.new_game.KMN_WINER_DICT[self.new_game.player1.choices[-1]]):
                '''User1 is winner in round'''
                self.new_game.player1_score += 1
            elif (self.new_game.player1.choices[-1] != self.new_game.player2.choices[-1]) and \
                (self.new_game.player1.choices[-1] in self.new_game.KMN_WINER_DICT[self.new_game.player2.choices[-1]]):
                '''user2 is winner round'''
                self.new_game.player2_score += 1
            if self.new_game.player1_score >= 5:
                '''Total winner User1'''
                self.new_game.winner_data = await self.new_game.get_winner_data(self.new_game.player1.username)
            elif self.new_game.player2_score >= 5:
                '''Total Winner User2'''
                self.new_game.winner_data = await self.new_game.get_winner_data(self.new_game.player2.username)
            message = jsons.dump(self.new_game)
        elif not self.new_game.winner_data and len(self.new_game.player1.choices) != len(self.new_game.player2.choices):
            '''Only one user make choice'''
            message = {'make_choice': user}
        else:
            '''winner is allready exist'''
            message = jsons.dump(self.new_game)
        print(message)
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


