import pickle

from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.cache import cache

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
        self.round_number = 1
        self.player1 = PlayerGame(user1)
        self.player2 = PlayerGame(user2)
        self.player1_is_round_win = []
        self.player2_is_round_win = []
        self.player1_score = 0
        self.player2_score = 0
        self.winner_data = ''
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
        return {'winner': self.winner_data}

    async def add_user_choice(self, username, choice):
        if username == self.player1.username:
            self.player1.make_choice(choice)
        else:
            self.player2.make_choice(choice)

    async def is_some_winner(self):
        if self.player1_score >= 5:
            '''Total winner User1'''
            self.winner_data = await self.get_winner_data(self.player1.username)
        elif self.player2_score >= 5:
            '''Total Winner User2'''
            self.winner_data = await self.get_winner_data(self.player2.username)

    async def is_round_winner(self):
        if self.player1.choices[-1] == self.player2.choices[-1]:
            '''no one winner'''
            self.player1_is_round_win.append(0)
            self.player2_is_round_win.append(0)
        elif (self.player1.choices[-1] != self.player2.choices[-1]) and \
                (self.player2.choices[-1] in self.KMN_WINER_DICT[self.player1.choices[-1]]):
            '''User1 is winner in round'''
            self.player1_score += 1
            self.player1_is_round_win.append(1)
            self.player2_is_round_win.append(0)
        elif (self.player1.choices[-1] != self.player2.choices[-1]) and \
                (self.player1.choices[-1] in self.KMN_WINER_DICT[self.player2.choices[-1]]):
            '''user2 is winner round'''
            self.player2_score += 1
            self.player1_is_round_win.append(0)
            self.player2_is_round_win.append(1)
        self.round_number += 1

    async def check_if_user_make_choice_or_win_round_or_win_game(self, user):
        if not self.winner_data and len(self.player1.choices) == len(self.player2.choices):
            '''both users make choice'''
            await self.is_round_winner()
            await self.is_some_winner()
            message = {
            'round_number' : self.round_number,
            'user1': {'username': self.player1.username, 'choice': self.player1.choices[-1],
                      'is_round_winner': self.player1_is_round_win[-1], 'score': self.player1_score},
            'user2': {'username': self.player2.username, 'choice': self.player2.choices[-1],
                      'is_round_winner': self.player2_is_round_win[-1], 'score': self.player2_score},
            'winner': self.winner_data}
        elif not self.winner_data and len(self.player1.choices) != len(self.player2.choices):
            '''Only one user make choice'''
            message = {'make_choice': user}
        else:
            '''winner is allready exist'''
            message = {'winner': self.winner_data}
        return message


async def serialize_and_put_to_cache(key, object):
    dumped = pickle.dumps(object)
    cache.set(key, dumped)


async def deserialize_and_get_from_cache(key):
    dumped = cache.get(key)
    instance =pickle.loads(dumped)
    return instance
