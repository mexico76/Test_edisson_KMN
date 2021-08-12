from django.urls import path
from . import views

urlpatterns = [
    path('', views.RegistrationView.as_view(), name='registration'),
]

