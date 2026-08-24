from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from dating.views import FeedView


class FeedFallbackTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='demo_user', password='testpass123')
        self.factory = RequestFactory()

    def test_feed_returns_fallback_recommendation_when_no_other_profiles_exist(self):
        request = self.factory.get('/dating/')
        request.user = self.user

        view = FeedView()
        view.request = request

        feed_items = view.get_queryset()

        self.assertTrue(feed_items)
        self.assertGreaterEqual(len(feed_items), 1)


class FeedPageChromeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='chrome_user', password='testpass123')
        self.user.profile.is_onboarded = True
        self.user.profile.save()
        self.client.login(username='chrome_user', password='testpass123')

    def test_feed_hides_bottom_nav_and_exposes_real_links(self):
        response = self.client.get(reverse('dating:feed'))

        self.assertContains(response, 'Редактировать профиль')
        self.assertContains(response, reverse('dating:profile_edit'))
        self.assertContains(response, reverse('dating:logout'))
        self.assertNotContains(response, '<nav class="bottom-nav">', html=False)
        self.assertNotContains(response, 'Совместимость 96%')
        self.assertContains(response, reverse('main:index'))
        self.assertContains(response, reverse('dating:chat_list'))
        self.assertContains(response, reverse('dating:groups'))
        self.assertContains(response, reverse('dating:feed'))
        self.assertContains(response, 'Культовая связь — это интеллектуальная платформа для знакомств и общения. Наш ИИ помогает найти человека, с которым у вас общие ценности, интересы и цели в жизни.')
