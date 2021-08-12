from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login

from registration.models import Player


def create_new_user(reg_form):
    try:
        user = User.objects.create_user(username=reg_form.cleaned_data.get('user_login'),
                                        email=reg_form.cleaned_data.get('user_email'),
                                        password=reg_form.cleaned_data.get('user_password'),
                                        first_name=reg_form.cleaned_data.get('user_name'),
                                        last_name=reg_form.cleaned_data.get('user_surname'), )
        return user
    except Exception as inst:
        return inst

def create_new_player(user, request, reg_form):
    try:
        player = Player.objects.create(user=user)
        player.save()
        return player
    except Exception as error_creating_player:
        if User.objects.get(username=reg_form.cleaned_data['user_login']).exists():
            user_to_delete = User.objects.get(username=user.username)
            user_to_delete.delete()
            return error_creating_player

def new_user_auto_loging(reg_form, request):
    new_user = authenticate(username=reg_form.cleaned_data['user_login'],
                            password=reg_form.cleaned_data['user_password'],
                            )
    if new_user is not None:
        sing_in = login(request, new_user)
        player_is_online = Player.objects.get(user=request.user)
        player_is_online.is_online = True
        player_is_online.save()
        return sing_in
    else:return 'there is no user'