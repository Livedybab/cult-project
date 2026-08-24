from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

def index(request):
    """Главная страница"""
    return render(request, 'main/index.html')

def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dating:list')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})