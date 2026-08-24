from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

GENDER_CHOICES = (
    ('M', 'Мужской'),
    ('F', 'Женский'),
)

LOOKING_FOR_CHOICES = (
    ('relationship', 'Отношения'),
    ('friends', 'Друзья'),
    ('communication', 'Общение'),
    ('business', 'Деловые знакомства'),
)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    age = models.PositiveSmallIntegerField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    looking_for = models.CharField(max_length=20, choices=LOOKING_FOR_CHOICES, blank=True, null=True)
    interests = models.ManyToManyField('Interest', blank=True, related_name='profiles')
    values = models.ManyToManyField('Value', blank=True, related_name='profiles')
    character_traits = models.ManyToManyField('CharacterTrait', blank=True, related_name='profiles')
    compatibility_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    is_onboarded = models.BooleanField(default=False)
    last_active = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

class Interest(models.Model):
    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

class Value(models.Model):
    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

class CharacterTrait(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Photo(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='profile_photos/')
    caption = models.CharField(max_length=200, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'uploaded_at']

class Like(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_given')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_received')
    created_at = models.DateTimeField(auto_now_add=True)
    is_like = models.BooleanField(default=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

class Chat(models.Model):
    participants = models.ManyToManyField(User, related_name='chats')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('dating:chat_detail', kwargs={'chat_id': self.id})

    def last_message(self):
        return self.messages.last()

    def __str__(self):
        return f"Chat {self.id}"

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

class DailyPick(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_picks')
    recommended_users = models.ManyToManyField(User, related_name='recommended_in_picks')
    date = models.DateField(auto_now_add=True)
    is_viewed = models.BooleanField(default=False)

    def __str__(self):
        return f"Подборка для {self.user.username} от {self.date}"

class Group(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    interests = models.ManyToManyField(Interest, related_name='groups')
    members = models.ManyToManyField(User, through='GroupMembership', related_name='dating_groups')
    image = models.ImageField(upload_to='groups/', blank=True, null=True)

    def __str__(self):
        return self.name

class GroupMembership(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

class Compatibility(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compat_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compat_user2')
    score = models.FloatField()
    explanation = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()