import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import DenyConnection
from django.contrib.auth.models import AnonymousUser, User
from django.db.models import Q

from registration.models import Player


class WaitingRoomConsumer(AsyncWebsocketConsumer):
    @database_sync_to_async
    def __change_online_status(self, status:bool=False):
        player = Player.objects.get(user=self.scope['user'])
        player.is_online = status
        player.save()

    @database_sync_to_async
    def __change_busy_status(self, status: bool = False):
        player = Player.objects.get(user=self.scope['user'])
        player.is_busy = status
        player.save()

    @database_sync_to_async
    def __change_busy_status_both_player(self, user1, user2, status: bool = False):
        player1 = Player.objects.get(user__username=user1)
        player1.is_busy = status
        player1.save()
        player2 = Player.objects.get(user__username=user2)
        player2.is_busy = status
        player2.save()

    @database_sync_to_async
    def __get_user_list_online(self):
        online_users = Player.objects.filter(Q(is_online=True) | Q(is_busy=True))
        user_list = tuple(
            {'username': user.user.username, 'id': user.user.pk, 'is_online': user.is_online, 'is_busy': user.is_busy}
        for user in online_users)
        return user_list

    #------------------------------------------------------help functions
    async def connect(self):
        await self.__change_busy_status(False)
        self.room_group_name = 'waiting_room'
        # Join room group
        if self.scope['user'] == AnonymousUser():
            raise DenyConnection("User is not exist")
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.__change_online_status(True)
        user_list = await self.__get_user_list_online()
        await self.receive({'user_list': user_list})
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        if type(text_data)==str:
            text_data = json.loads(text_data)
        message_dict = {}
        if 'invite_user' in text_data.keys():
            await self.__change_busy_status_both_player(text_data['invite_user']['requester'],
                                                        text_data['invite_user']['receiver'], True)
            message_dict['invite_user'] = {'requester': text_data['invite_user']['requester'],
                                           'receiver': text_data['invite_user']['receiver']}
        if 'reject_user' in text_data.keys():
            await self.__change_busy_status_both_player(text_data['reject_user']['rejector'],
                                                        text_data['reject_user']['requester'], False)
            message_dict['reject_user'] = {'rejector': text_data['reject_user']['rejector'],
                                           'requester': text_data['reject_user']['requester']}
        if 'reject_from_requester' in text_data.keys():
            await self.__change_busy_status_both_player(text_data['reject_from_requester']['receiver'],
                                                        text_data['reject_from_requester']['requester'], False)
            message_dict['reject_from_requester'] = {'receiver': text_data['reject_from_requester']['receiver'],
                                           'requester': text_data['reject_from_requester']['requester']}
        if 'agree_for_game_to_server' in text_data.keys():
            message_dict['agree_for_game_to_server'] = {'requester': text_data['agree_for_game_to_server']['requester'],
                                           'receiver': text_data['agree_for_game_to_server']['receiver']}

        user_list = await self.__get_user_list_online()
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
        await self.__change_online_status(False)
        user_list = await self.__get_user_list_online()
        await self.receive({'user_list': user_list})
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

class GameConsumer(AsyncWebsocketConsumer):
    '''Consumer for gaming'''

    KMN_DICT = {
        0: 'No Choice',
        1: 'Stone',
        2: 'Scissors',
        3: 'Paper',
        4: 'Lizard',
        5: 'Spok'
    }
    KMN_WINER_DICT = {
        0: [],
        1: [2, 4, 0],
        2: [3, 4, 0],
        3: [1, 5, 0],
        4: [3, 5, 0],
        5: [1, 2, 0]
    }
    GAME_DICT = {
        'user1': {'username': '', 'choice': [], 'is_round_winner': []},
        'user2': {'username': '', 'choice': [], 'is_round_winner': []},
        'winner': []
    }
    @database_sync_to_async
    def __change_busy_status(self, status: bool = False):
        player = Player.objects.get(user=self.scope['user'])
        player.is_busy = status
        player.save()

    @database_sync_to_async
    def __get_winner_data(self, username):
        user = User.objects.filter(username=username).first()
        return [user.username, user.first_name, user.last_name]

    async def connect(self):
        self.user1 = self.scope['url_route']['kwargs']['user1']
        self.user2 = self.scope['url_route']['kwargs']['user2']
        self.room_group_name = f'game-{self.user1}-{self.user2}'
        self.GAME_DICT['user1']['username'] = self.user1
        self.GAME_DICT['user2']['username'] = self.user2
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.__change_busy_status(False)
        # print('GAME_DICT: ', self.GAME_DICT)
        self.GAME_DICT = {
            'user1': {'username': '', 'choice': [], 'is_round_winner': []},
            'user2': {'username': '', 'choice': [], 'is_round_winner': []},
            'winner': []
        }
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,

        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        if type(text_data)==str:
            text_data = json.loads(text_data)
        # Send message to room group
        user = text_data['user'] # curent user
        choice = text_data['choice']
        if self.GAME_DICT['winner'] == []:
            if user == self.GAME_DICT['user1']['username'] :
                self.GAME_DICT['user1']['choice'].append((choice))
            else: #user == self.GAME_DICT['user2']['username']:
                self.GAME_DICT['user2']['choice'].append((choice))
            if len(self.GAME_DICT['user1']['choice']) == len(self.GAME_DICT['user2']['choice']):
                '''both users make choice'''
                if self.GAME_DICT['user2']['choice'][-1] == self.GAME_DICT['user1']['choice'][-1]:
                    '''no one winner'''
                    self.GAME_DICT['user1']['is_round_winner'].append(0)
                    self.GAME_DICT['user2']['is_round_winner'].append(0)
                elif self.GAME_DICT['user2']['choice'][-1] in self.KMN_WINER_DICT[self.GAME_DICT['user1']['choice'][-1]]:
                    '''User1 is winner in round'''
                    self.GAME_DICT['user1']['is_round_winner'].append(1)
                    self.GAME_DICT['user2']['is_round_winner'].append(0)
                else:
                    '''user2 is winner round'''
                    self.GAME_DICT['user1']['is_round_winner'].append(0)
                    self.GAME_DICT['user2']['is_round_winner'].append(1)
                if self.GAME_DICT['user1']['is_round_winner'].count(1) >= 5:
                    '''Total winner User1'''
                    winner_data = await self.__get_winner_data(self.GAME_DICT['user1']['username'])
                    self.GAME_DICT['winner'] = winner_data
                elif self.GAME_DICT['user2']['is_round_winner'].count(1) >= 5:
                    '''Total Winner User2'''
                    winner_data = await self.__get_winner_data(self.GAME_DICT['user2']['username'])
                    self.GAME_DICT['winner'] = winner_data
                message = self.GAME_DICT
                print(self.GAME_DICT)
            else:
                '''Only one user make choice'''
                if len(self.GAME_DICT['user1']['choice']) > len(self.GAME_DICT['user2']['choice']):
                    message = {'make_choice': self.GAME_DICT['user1']['username']}
                else:
                    message = {'make_choice': self.GAME_DICT['user2']['username']}
        else:
            '''Winner is allready exist'''
            message = {'winner': self.GAME_DICT['winner']}
            # print(self.GAME_DICT)
        # print('game_DICT', self.GAME_DICT)
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
    if disconnect:
        GAME_DICT = {
            'user1': {'username': '', 'choice': [], 'is_round_winner': []},
            'user2': {'username': '', 'choice': [], 'is_round_winner': []},
            'winner': []
        }