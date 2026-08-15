from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("learning", "0007_quiz_reading_text"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="avatar",
            field=models.ImageField(blank=True, upload_to="avatars/", verbose_name="аватар"),
        ),
        migrations.AddField(
            model_name="profile",
            name="learning_goal",
            field=models.CharField(blank=True, max_length=180, verbose_name="ціль навчання"),
        ),
        migrations.CreateModel(
            name="VocabularySet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180, verbose_name="назва списку")),
                ("description", models.TextField(blank=True, verbose_name="пояснення")),
                ("order", models.PositiveIntegerField(default=1, verbose_name="порядок")),
                ("is_published", models.BooleanField(default=True, verbose_name="опубліковано")),
                ("lesson", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="vocabulary_sets", to="learning.lesson", verbose_name="урок")),
            ],
            options={
                "verbose_name": "список слів",
                "verbose_name_plural": "списки слів",
                "ordering": ["lesson", "order", "title"],
            },
        ),
        migrations.CreateModel(
            name="VocabularyWord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("word", models.CharField(max_length=140, verbose_name="слово або фраза")),
                ("translation", models.CharField(blank=True, max_length=220, verbose_name="переклад / пояснення")),
                ("example", models.TextField(blank=True, verbose_name="приклад")),
                ("order", models.PositiveIntegerField(default=1, verbose_name="порядок")),
                ("vocabulary_set", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="words", to="learning.vocabularyset", verbose_name="список")),
            ],
            options={
                "verbose_name": "слово",
                "verbose_name_plural": "слова",
                "ordering": ["vocabulary_set", "order", "word"],
            },
        ),
        migrations.CreateModel(
            name="StudentWord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("unknown", "Не знаю"), ("learning", "Вчу"), ("known", "Знаю")], default="unknown", max_length=20, verbose_name="статус")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="додано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="оновлено")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="word_progress", to=settings.AUTH_USER_MODEL, verbose_name="учень")),
                ("word", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="student_progress", to="learning.vocabularyword", verbose_name="слово")),
            ],
            options={
                "verbose_name": "слово учня",
                "verbose_name_plural": "слова учнів",
                "ordering": ["-updated_at"],
                "unique_together": {("student", "word")},
            },
        ),
    ]
