from django.db import models
from django.contrib.auth.models import User

class Player(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_online = models.BooleanField(default=False)
    is_busy = models.BooleanField(default=False)

    class Meta:
        def __str__(self):
            return f'{self.user.username}'