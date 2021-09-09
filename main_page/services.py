import jsons
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User
from django.db.models import Q
from django_redis import cache

from registration.models import Player


class WaitingRoom:
    @database_sync_to_async
    def change_busy_status_both_player(self, user1, user2, status: bool = False):
        player1 = Player.objects.get(user__username=user1)
        player1.is_busy = status
        player1.save()
        player2 = Player.objects.get(user__username=user2)
        player2.is_busy = status
        player2.save()

    @database_sync_to_async
    def get_user_list_online(self):
        online_users = Player.objects.filter(Q(is_online=True) | Q(is_busy=True))
        user_list = tuple(
            {'username': user.user.username, 'id': user.user.pk, 'is_online': user.is_online, 'is_busy': user.is_busy}
            for user in online_users)
        return user_list

    async def invite_logic(self, text_data, message_dict):
        if 'invite_user' in text_data.keys():
            await self.change_busy_status_both_player(text_data['invite_user']['requester'],
                                                        text_data['invite_user']['receiver'], True)
            message_dict['invite_user'] = {'requester': text_data['invite_user']['requester'],
                                           'receiver': text_data['invite_user']['receiver']}
        elif 'reject_user' in text_data.keys():
            await self.change_busy_status_both_player(text_data['reject_user']['rejector'],
                                                        text_data['reject_user']['requester'], False)
            message_dict['reject_user'] = {'rejector': text_data['reject_user']['rejector'],
                                           'requester': text_data['reject_user']['requester']}
        elif 'reject_from_requester' in text_data.keys():
            await self.change_busy_status_both_player(text_data['reject_from_requester']['receiver'],
                                                        text_data['reject_from_requester']['requester'], False)
            message_dict['reject_from_requester'] = {'receiver': text_data['reject_from_requester']['receiver'],
                                           'requester': text_data['reject_from_requester']['requester']}
        elif 'agree_for_game_to_server' in text_data.keys():
            message_dict['agree_for_game_to_server'] = {'requester': text_data['agree_for_game_to_server']['requester'],
                                           'receiver': text_data['agree_for_game_to_server']['receiver']}
        return message_dict


class PlayerGame:
    def __init__(self, username: str = None):
        self.username = username
        self.choices = []

    @database_sync_to_async
    def change_online_status(self, status: bool = False):
        player = Player.objects.get(user=self.username)
        player.is_online = status
        player.save()

    @database_sync_to_async
    def change_busy_status(self, status: bool = False):
        player = Player.objects.get(user=self.username)
        player.is_busy = status
        player.save()

    def make_choice(self, choice:int=None):
        self.choices.append(choice)


class Game:
    def __init__(self, user1, user2):
        self.player1 = PlayerGame(user1)
        self.player2 = PlayerGame(user2)
        self.player1_score = 0
        self.player2_score = 0
        self.winner_data = None
        self.KMN_DICT = {
            0: 'No Choice',
            1: 'Stone',
            2: 'Scissors',
            3: 'Paper',
            4: 'Lizard',
            5: 'Spok'
        }
        self.KMN_WINER_DICT = {
            0: (),
            1: (2, 4, 0),
            2: (3, 4, 0),
            3: (1, 5, 0),
            4: (3, 5, 0),
            5: (1, 2, 0)
        }

    @database_sync_to_async
    def get_winner_data(self, username):
        user = User.objects.filter(username=username).first()
        return f'Username - {user.username}, firstname - {user.first_name}, lastname - {user.last_name}.'

    async def if_user_disconnect(self, username):
        if self.player1_score < 5 and username == self.player1.username:
            winner_data = await self.get_winner_data(self.player2.username)
            self.winner_data = winner_data + (f' \n{self.player1.username} was disconnected! ')
        else:
            winner_data = await self.get_winner_data(self.player1.username)
            self.winner_data = winner_data + (f' \n{self.player2.username} was disconnected! ')
        return self

    async def add_user_choice(self, username, choice):
        if username == self.player1.username:
            self.player1.make_choice(choice)
        else:
            self.player2.make_choice(choice)


async def serialize_and_put_to_cache(key, object):
    dumped = jsons.dump(object)
    print(dumped)
    cache.set(key, dumped)


async def deserialize_and_get_from_cache(key, class_inst):
    dumped = cache.get(key)
    instance =jsons.load(dumped, class_inst)
    return instance
