from django.contrib.auth.decorators import login_required
from django.urls import path

from .views import index, game, Login, Logout

urlpatterns = [
    path('', login_required(index, 'login'), name='index'),
    path('login', Login.as_view(), name='login'),
    path('logout', Logout.as_view(), name='logout'),
    path('game/<str:user1>-<str:user2>/', login_required(game, 'login'), name='game')
]