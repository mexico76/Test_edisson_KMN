from django.contrib import admin

from .models import Player

class PlayerAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_online', 'is_busy')

admin.site.register(Player, PlayerAdmin)
