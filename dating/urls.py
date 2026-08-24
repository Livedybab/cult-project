from django.urls import path
from . import views

app_name = 'dating'

urlpatterns = [
    # Главная лента
    path('', views.FeedView.as_view(), name='feed'),
    # Свайп
    path('swipe/', views.SwipeView.as_view(), name='swipe'),
    path('swipe/action/', views.swipe_action, name='swipe_action'),
    # Чаты
    path('chats/', views.chat_list, name='chat_list'),
    path('chats/<int:chat_id>/', views.chat_detail, name='chat_detail'),
    # Профиль
    path('profile/<int:pk>/', views.ProfileDetailView.as_view(), name='profile_detail'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/photo/delete/<int:photo_id>/', views.profile_photo_delete, name='profile_photo_delete'),
    # Онбординг
    path('onboarding/<int:step>/', views.onboarding, name='onboarding'),
    path('onboarding/', views.onboarding, name='onboarding_start'),
    # Группы
    path('groups/', views.GroupListView.as_view(), name='groups'),
    # Ежедневная подборка
    path('daily-pick/', views.DailyPickView.as_view(), name='daily_pick'),
    # Аутентификация
    path('login/', views.dating_login, name='login'),
    path('register/', views.dating_register, name='register'),
    path('logout/', views.dating_logout, name='logout'),
]