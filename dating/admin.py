from django.contrib import admin
from .models import Profile, Photo, Like, Chat, Message, Interest, Value, CharacterTrait, DailyPick, Group, Compatibility

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'gender', 'city', 'is_onboarded')
    search_fields = ('user__username', 'city')

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Value)
class ValueAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(CharacterTrait)
class CharacterTraitAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(DailyPick)
class DailyPickAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'is_viewed')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Compatibility)
class CompatibilityAdmin(admin.ModelAdmin):
    list_display = ('user1', 'user2', 'score')