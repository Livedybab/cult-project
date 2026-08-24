import io
import os
import random

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from dating.models import (
    Profile, Interest, Value, CharacterTrait, Like,
)

INTERESTS = [
    "Книги", "Путешествия", "Спорт", "Музыка", "Кино", "Искусство",
    "Кулинария", "Йога", "Фотография", "Технологии", "Психология",
    "Природа", "Танцы", "Волонтёрство", "Настольные игры", "Карьера",
    "Медитация", "Киберспорт", "Мода", "Наука",
]

VALUES = [
    "Честность", "Семья", "Свобода", "Развитие", "Дружба", "Творчество",
    "Стабильность", "Открытость", "Ответственность", "Юмор",
]

TRAITS = [
    "Добрый", "Целеустремлённый", "Заботливый", "Легкий на подъём",
    "Аналитичный", "Романтичный", "Спокойный", "Энергичный",
    "Любопытный", "Надёжный",
]

CITIES = [
    "Москва", "Санкт-Петербург", "Казань", "Новосибирск", "Екатеринбург",
    "Краснодар", "Зеленоград", "Калининград", "Сочи", "Уфа",
]

BIOS = [
    "Люблю глубокие разговоры и воскресные прогулки.",
    "Ищу человека, с которым интересно молчать и смеяться.",
    "Постоянно учусь новому и пробую странные рецепты.",
    "Мечтатель с приземлённым подходом к жизни.",
    "Ценю искренность, юмор и хороший кофе.",
    "Спокойный, надёжный, немного философский.",
    "Энергии много, планов ещё больше.",
    "Верю, что близость — это про общие смыслы.",
]

GRADIENTS = [
    ("#6D28D9", "#D946EF"), ("#2563EB", "#22D3EE"), ("#DB2777", "#F97316"),
    ("#059669", "#A3E635"), ("#7C3AED", "#EC4899"), ("#0EA5E9", "#6366F1"),
    ("#E11D48", "#FB923C"), ("#10B981", "#34D399"),
]


def make_avatar(username, color1, color2, initial):
    from PIL import Image, ImageDraw, ImageFont

    width, height = 600, 800
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    steps = 60
    for i in range(steps):
        t = i / (steps - 1)
        r = int(int(color1[1:3], 16) * (1 - t) + int(color2[1:3], 16) * t)
        g = int(int(color1[3:5], 16) * (1 - t) + int(color2[3:5], 16) * t)
        b = int(int(color1[5:7], 16) * (1 - t) + int(color2[5:7], 16) * t)
        draw.line([(0, int(height * i / steps)), (width, int(height * i / steps))],
                  fill=(r, g, b))

    circle_color = (255, 255, 255)
    cx, cy, rad = width // 2, height // 2 - 40, 150
    draw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad],
                 fill=circle_color)

    try:
        font = ImageFont.truetype("arial.ttf", 200)
    except Exception:
        font = ImageFont.load_default()

    text_color = (int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16))
    text_bbox = draw.textbbox((0, 0), initial, font=font)
    tx = cx - (text_bbox[2] - text_bbox[0]) / 2 - text_bbox[0]
    ty = cy - (text_bbox[3] - text_bbox[1]) / 2 - text_bbox[1]
    draw.text((tx, ty), initial, font=font, fill=text_color)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return ContentFile(buf.getvalue())


class Command(BaseCommand):
    help = "Генерирует тестовых пользователей с анкетами и аватарами для проверки свайпов."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=12,
                            help="Сколько тестовых пользователей создать.")
        parser.add_argument("--password", type=str, default="testpass123",
                            help="Пароль для всех тестовых аккаунтов.")
        parser.add_argument("--clear", action="store_true",
                            help="Удалить ранее созданных тестовых пользователей (testuser*).")

    def handle(self, *args, **options):
        count = options["count"]
        password = options["password"]

        if options["clear"]:
            deleted, _ = User.objects.filter(username__startswith="testuser").delete()
            self.stdout.write(self.style.WARNING(f"Удалено тестовых пользователей: {deleted}"))

        # Базовая таксономия (интересы/ценности/черты)
        interests = [Interest.objects.get_or_create(name=n)[0] for n in INTERESTS]
        values = [Value.objects.get_or_create(name=n)[0] for n in VALUES]
        traits = [CharacterTrait.objects.get_or_create(name=n)[0] for n in TRAITS]

        created = 0
        existing = User.objects.filter(username__startswith="testuser").count()
        for i in range(count):
            username = f"testuser{existing + i + 1}"
            if User.objects.filter(username=username).exists():
                continue

            user = User.objects.create_user(
                username=username,
                email=f"{username}@example.com",
                password=password,
            )

            profile = user.profile
            profile.age = random.randint(19, 44)
            profile.gender = random.choice(["M", "F"])
            profile.city = random.choice(CITIES)
            profile.bio = random.choice(BIOS)
            profile.looking_for = random.choice(["relationship", "friends", "communication"])
            profile.is_onboarded = True
            profile.save()

            profile.interests.set(random.sample(interests, random.randint(3, 6)))
            profile.values.set(random.sample(values, random.randint(2, 4)))
            profile.character_traits.set(random.sample(traits, random.randint(2, 4)))

            color1, color2 = random.choice(GRADIENTS)
            initial = username[0].upper()
            avatar = make_avatar(username, color1, color2, initial)
            profile.avatar.save(f"{username}.png", avatar, save=True)

            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Создано тестовых пользователей: {created}. "
            f"Логин: testuser<N>, пароль: {password}"
        ))
        self.stdout.write("Зайдите под любым из них и откройте /swipe/ для проверки свайпов.")
