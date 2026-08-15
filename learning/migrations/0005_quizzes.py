from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("learning", "0004_parent_child"),
    ]

    operations = [
        migrations.CreateModel(
            name="Quiz",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180, verbose_name="назва тесту")),
                ("description", models.TextField(blank=True, verbose_name="опис")),
                ("max_points", models.PositiveIntegerField(default=100, verbose_name="максимум балів")),
                ("passing_percent", models.PositiveIntegerField(default=60, verbose_name="прохідний відсоток")),
                ("is_published", models.BooleanField(default=True, verbose_name="опубліковано")),
                ("allow_retakes", models.BooleanField(default=True, verbose_name="дозволити повторне проходження")),
                ("order", models.PositiveIntegerField(default=1, verbose_name="порядок")),
                ("lesson", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="quizzes", to="learning.lesson", verbose_name="урок")),
            ],
            options={
                "verbose_name": "тест",
                "verbose_name_plural": "тести",
                "ordering": ["lesson", "order", "title"],
            },
        ),
        migrations.CreateModel(
            name="QuizQuestion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.TextField(verbose_name="питання")),
                ("explanation", models.TextField(blank=True, verbose_name="пояснення після відповіді")),
                ("order", models.PositiveIntegerField(default=1, verbose_name="порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="активне")),
                ("quiz", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="questions", to="learning.quiz", verbose_name="тест")),
            ],
            options={
                "verbose_name": "питання тесту",
                "verbose_name_plural": "питання тестів",
                "ordering": ["quiz", "order", "id"],
            },
        ),
        migrations.CreateModel(
            name="QuizAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("correct_count", models.PositiveIntegerField(default=0, verbose_name="правильних відповідей")),
                ("total_count", models.PositiveIntegerField(default=0, verbose_name="усього питань")),
                ("score_percent", models.PositiveIntegerField(default=0, verbose_name="відсоток")),
                ("points", models.PositiveIntegerField(default=0, verbose_name="бали")),
                ("started_at", models.DateTimeField(auto_now_add=True, verbose_name="розпочато")),
                ("completed_at", models.DateTimeField(auto_now=True, verbose_name="завершено")),
                ("quiz", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempts", to="learning.quiz", verbose_name="тест")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="quiz_attempts", to=settings.AUTH_USER_MODEL, verbose_name="учень")),
            ],
            options={
                "verbose_name": "результат тесту",
                "verbose_name_plural": "результати тестів",
                "ordering": ["-completed_at"],
            },
        ),
        migrations.CreateModel(
            name="QuizChoice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.CharField(max_length=255, verbose_name="варіант відповіді")),
                ("is_correct", models.BooleanField(default=False, verbose_name="правильна відповідь")),
                ("order", models.PositiveIntegerField(default=1, verbose_name="порядок")),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="choices", to="learning.quizquestion", verbose_name="питання")),
            ],
            options={
                "verbose_name": "варіант відповіді",
                "verbose_name_plural": "варіанти відповідей",
                "ordering": ["question", "order", "id"],
            },
        ),
        migrations.CreateModel(
            name="QuizAnswer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_correct", models.BooleanField(default=False, verbose_name="правильно")),
                ("attempt", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="learning.quizattempt", verbose_name="спроба")),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="learning.quizquestion", verbose_name="питання")),
                ("selected_choice", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="answers", to="learning.quizchoice", verbose_name="обрана відповідь")),
            ],
            options={
                "verbose_name": "відповідь у тесті",
                "verbose_name_plural": "відповіді у тестах",
                "ordering": ["attempt", "question__order", "question_id"],
            },
        ),
    ]
