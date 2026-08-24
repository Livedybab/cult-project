import random
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Count, Q
from .models import (
    Profile, Photo, Like, Chat, Message, Interest, Value,
    CharacterTrait, DailyPick, Group, Compatibility
)
from .forms import (
    OnboardingStep1Form, OnboardingStep2Form,
    OnboardingStep3Form, OnboardingStep4Form,
    ProfileForm, PhotoForm
)

logger = logging.getLogger(__name__)


# ===== АУТЕНТИФИКАЦИЯ =====
def dating_login(request):
    if request.user.is_authenticated:
        return redirect('dating:feed')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dating:feed')
    else:
        form = AuthenticationForm()
    return render(request, 'dating/login.html', {'form': form})


def dating_register(request):
    if request.user.is_authenticated:
        return redirect('dating:feed')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dating:onboarding_start')
    else:
        form = UserCreationForm()
    return render(request, 'dating/register.html', {'form': form})


def dating_logout(request):
    logout(request)
    return redirect('dating:login')


# ===== ФУНКЦИЯ СОВМЕСТИМОСТИ =====
def calculate_compatibility(profile1, profile2):
    score = 0
    max_score = 0
    interests1 = set(profile1.interests.all())
    interests2 = set(profile2.interests.all())
    max_score += 10
    if interests1 and interests2:
        common = len(interests1 & interests2)
        total = len(interests1 | interests2)
        score += int((common / total) * 10) if total > 0 else 0
    values1 = set(profile1.values.all())
    values2 = set(profile2.values.all())
    max_score += 10
    if values1 and values2:
        common = len(values1 & values2)
        total = len(values1 | values2)
        score += int((common / total) * 10) if total > 0 else 0
    traits1 = set(profile1.character_traits.all())
    traits2 = set(profile2.character_traits.all())
    max_score += 10
    if traits1 and traits2:
        common = len(traits1 & traits2)
        total = len(traits1 | traits2)
        score += int((common / total) * 10) if total > 0 else 0
    return int((score / max_score) * 100) if max_score > 0 else 0


# ===== ОНБОРДИНГ =====
@login_required
def onboarding(request, step=1):
    profile = request.user.profile
    total_steps = 4

    if request.method == 'POST':
        if step == 1:
            form = OnboardingStep1Form(request.POST, instance=profile)
        elif step == 2:
            form = OnboardingStep2Form(request.POST, instance=profile)
        elif step == 3:
            form = OnboardingStep3Form(request.POST, instance=profile)
        elif step == 4:
            form = OnboardingStep4Form(request.POST, instance=profile)

        if form.is_valid():
            if step == 3:
                profile.interests.set(form.cleaned_data['interests'])
                profile.values.set(form.cleaned_data['values'])
                profile.save()
            elif step == 4:
                profile.character_traits.set(form.cleaned_data['character_traits'])
                profile.save()
            else:
                form.save()
            if step == total_steps:
                profile.is_onboarded = True
                profile.save()
                return redirect('dating:feed')
            else:
                return redirect('dating:onboarding', step=step+1)
    else:
        if step == 1:
            form = OnboardingStep1Form(instance=profile)
        elif step == 2:
            form = OnboardingStep2Form(instance=profile)
        elif step == 3:
            initial = {'interests': profile.interests.all(), 'values': profile.values.all()}
            form = OnboardingStep3Form(initial=initial, instance=profile)
        elif step == 4:
            initial = {'character_traits': profile.character_traits.all()}
            form = OnboardingStep4Form(initial=initial, instance=profile)
        else:
            return redirect('dating:feed')

    return render(request, 'dating/onboarding.html', {
        'form': form,
        'step': step,
        'total_steps': total_steps,
        'step_title': ['Основные данные', 'Цели и описание', 'Интересы и ценности', 'Характер'][step-1],
    })


# ===== FEED (ГЛАВНАЯ ЛЕНТА) =====
class FeedView(ListView):
    model = Profile
    template_name = 'dating/feed.html'
    context_object_name = 'feed_items'

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if response.status_code == 302:
            return response
        if request.user.is_authenticated and not request.user.profile.is_onboarded:
            return redirect('dating:onboarding_start')
        return response

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return []
        profiles = Profile.objects.exclude(user=user).filter(is_onboarded=True)

        if not profiles.exists():
            demo_username = 'cult_demo_match'
            demo_user, _ = User.objects.get_or_create(username=demo_username)
            demo_profile, _ = Profile.objects.get_or_create(
                user=demo_user,
                defaults={
                    'bio': 'Новых рекомендаций пока нет. Новые знакомства появятся как только соберётся больше участников.',
                    'city': 'Зеленоград',
                    'is_onboarded': True,
                }
            )
            return [(demo_profile, 0)]

        compat_list = []
        for p in profiles:
            score = calculate_compatibility(user.profile, p)
            compat_list.append((p, score))
        compat_list.sort(key=lambda x: x[1], reverse=True)
        return compat_list[:20]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['is_landing'] = not user.is_authenticated
        context['bottom_nav_inline'] = user.is_authenticated
        if user.is_authenticated:
            today = timezone.now().date()
            daily_pick = DailyPick.objects.filter(user=user, date=today).first()
            if not daily_pick:
                profiles = Profile.objects.exclude(user=user).filter(is_onboarded=True).order_by('?')[:5]
                daily_pick = DailyPick.objects.create(user=user)
                daily_pick.recommended_users.set([p.user for p in profiles])
            context['daily_pick'] = daily_pick
        context['groups'] = Group.objects.all()[:5]
        return context


# ===== СВАЙП =====
class SwipeView(LoginRequiredMixin, ListView):
    model = Profile
    template_name = 'dating/swipe.html'
    context_object_name = 'profile'
    login_url = 'dating:login'

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if response.status_code == 302:
            return response
        if not request.user.profile.is_onboarded:
            return redirect('dating:onboarding_start')
        return response

    def get_queryset(self):
        user = self.request.user
        liked_users = Like.objects.filter(from_user=user).values_list('to_user_id', flat=True)
        return Profile.objects.filter(is_onboarded=True).exclude(user=user).exclude(user_id__in=liked_users)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        if qs.exists():
            profile = random.choice(qs)
            compatibility = calculate_compatibility(self.request.user.profile, profile)
            context['profile'] = profile
            context['compatibility'] = compatibility
        else:
            context['profile'] = None
            context['compatibility'] = 0
        return context


@login_required
def swipe_action(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()
    
    to_user_id = request.POST.get('user_id')
    action = request.POST.get('action')
    
    if not to_user_id or action not in ('like', 'dislike'):
        return JsonResponse({'error': 'Неверные данные'}, status=400)
    
    try:
        to_user = get_object_or_404(User, id=to_user_id)
        like, created = Like.objects.get_or_create(from_user=request.user, to_user=to_user)
        like.is_like = (action == 'like')
        like.save()
        
        if action == 'like':
            mutual_like = Like.objects.filter(from_user=to_user, to_user=request.user, is_like=True).exists()
            if mutual_like:
                chat = Chat.objects.filter(participants=request.user).filter(participants=to_user).first()
                if not chat:
                    chat = Chat.objects.create()
                    chat.participants.add(request.user, to_user)
                return JsonResponse({'status': 'match', 'chat_url': chat.get_absolute_url()})
        
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        logger.error(f"Ошибка в swipe_action: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


# ===== ЧАТЫ =====
@login_required
def chat_list(request):
    chats = request.user.chats.all().order_by('-updated_at').prefetch_related('messages')
    return render(request, 'dating/chat_list.html', {'chats': chats})


@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id, participants=request.user)
    Message.objects.filter(chat=chat, is_read=False).exclude(sender=request.user).update(is_read=True)
    
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            Message.objects.create(chat=chat, sender=request.user, text=text)
            chat.updated_at = timezone.now()
            chat.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'ok'})
            return redirect('dating:chat_detail', chat_id=chat.id)
    
    messages = chat.messages.all()
    return render(request, 'dating/chat_detail.html', {'chat': chat, 'messages': messages})


# ===== ПРОФИЛЬ =====
class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'dating/profile_detail.html'
    context_object_name = 'profile'
    login_url = 'dating:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_user = self.request.user
        if current_user != self.object.user:
            compat_score = calculate_compatibility(current_user.profile, self.object)
            context['compatibility_score'] = compat_score
            context['compatibility_explanation'] = "У вас много общего в интересах и ценностях!"
        else:
            context['compatibility_score'] = None
        return context


@login_required
def profile_edit(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('dating:profile_detail', pk=profile.pk)
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'dating/profile_edit.html', {'form': form})


@login_required
def profile_photo_delete(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id, profile=request.user.profile)
    photo.delete()
    return redirect('dating:profile_edit')


# ===== ГРУППЫ =====
class GroupListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = 'dating/groups.html'
    context_object_name = 'groups'
    login_url = 'dating:login'


# ===== ЕЖЕДНЕВНАЯ ПОДБОРКА =====
class DailyPickView(LoginRequiredMixin, DetailView):
    model = DailyPick
    template_name = 'dating/daily_pick.html'
    context_object_name = 'pick'
    login_url = 'dating:login'

    def get_object(self):
        today = timezone.now().date()
        pick, created = DailyPick.objects.get_or_create(user=self.request.user, date=today)
        if not created:
            pick.is_viewed = True
            pick.save()
        return pick

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recommended_profiles'] = [p.user.profile for p in self.object.recommended_users.all()]
        return context