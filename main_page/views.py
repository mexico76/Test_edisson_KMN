from django.shortcuts import render, redirect
from django.views.generic.base import View
from django.contrib.auth import login, logout, authenticate

from registration.models import Player
from .forms import LoginForm


def index(request):
    form = LoginForm()
    user = request.user
    users_online = Player.objects.filter(is_online=True)
    context = {'form': form, 'user': user, 'enemy_users': users_online}
    return render(request, 'main_page/index.html', context)


def game(request, user1, user2):
    if Player.objects.get(user__username=user1).is_busy == True and \
            Player.objects.get(user__username=user2).is_busy == True and\
            (request.user.username == user1 or request.user.username == user2):
        context = {'user1': user1, 'user2': user2, 'curent_user': request.user}
        return render(request, 'main_page/game.html', context)
    else:
        return render(request, 'main_page/wrong_game_path.html')


class Login(View):
    form = LoginForm()

    def get(self, request):
        context = {'form': self.form}
        return render(request, 'main_page/login_form.html', context)

    def post(self, request):
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                # correct username and password login the user
                login(request, user)
                return redirect('index')
            else:
                context = {'form': self.form}
                return render(request, 'main_page/wrong_login.html', context)


class Logout(View):
    def get(self, request):
        logout(request)
        return redirect('index')
