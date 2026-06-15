from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Course",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=160, verbose_name="назва")),
                ("direction", models.CharField(choices=[("english", "Англійська мова"), ("robotics", "Робототехніка"), ("web", "Веб-програмування")], max_length=20, verbose_name="напрям")),
                ("age_range", models.CharField(max_length=80, verbose_name="вік")),
                ("level", models.CharField(blank=True, max_length=80, verbose_name="рівень")),
                ("schedule", models.CharField(max_length=120, verbose_name="частота занять")),
                ("price", models.CharField(max_length=120, verbose_name="вартість")),
                ("final_project", models.CharField(max_length=180, verbose_name="підсумок")),
                ("short_description", models.TextField(verbose_name="короткий опис")),
                ("is_published", models.BooleanField(default=True, verbose_name="опубліковано")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="створено")),
            ],
            options={"verbose_name": "курс", "verbose_name_plural": "курси", "ordering": ["title"]},
        ),
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("student", "Учень"), ("parent", "Батьки"), ("teacher", "Викладач")], default="student", max_length=20, verbose_name="роль")),
                ("phone", models.CharField(blank=True, max_length=32, verbose_name="телефон")),
                ("child_name", models.CharField(blank=True, max_length=120, verbose_name="ім'я дитини")),
                ("parent_name", models.CharField(blank=True, max_length=120, verbose_name="ім'я одного з батьків")),
                ("birth_date", models.DateField(blank=True, null=True, verbose_name="дата народження")),
                ("notes", models.TextField(blank=True, verbose_name="нотатки")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "профіль", "verbose_name_plural": "профілі"},
        ),
        migrations.CreateModel(
            name="Enrollment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("started_at", models.DateField(verbose_name="дата старту")),
                ("is_active", models.BooleanField(default=True, verbose_name="активне навчання")),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to="learning.course", verbose_name="курс")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to=settings.AUTH_USER_MODEL, verbose_name="учень")),
            ],
            options={"verbose_name": "зарахування", "verbose_name_plural": "зарахування", "unique_together": {("student", "course")}},
        ),
        migrations.CreateModel(
            name="Module",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=160, verbose_name="назва")),
                ("description", models.TextField(blank=True, verbose_name="опис")),
                ("order", models.PositiveIntegerField(default=1, verbose_name="порядок")),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="modules", to="learning.course", verbose_name="курс")),
            ],
            options={"verbose_name": "модуль", "verbose_name_plural": "модулі", "ordering": ["course", "order"]},
        ),
        migrations.CreateModel(
            name="Lesson",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180, verbose_name="назва")),
                ("summary", models.TextField(blank=True, verbose_name="коротко про урок")),
                ("content", models.TextField(blank=True, verbose_name="матеріал уроку")),
                ("video_url", models.URLField(blank=True, verbose_name="відео або зустріч")),
                ("order", models.PositiveIntegerField(default=1, verbose_name="порядок")),
                ("is_available", models.BooleanField(default=True, verbose_name="доступний")),
                ("module", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lessons", to="learning.module", verbose_name="модуль")),
            ],
            options={"verbose_name": "урок", "verbose_name_plural": "уроки", "ordering": ["module", "order"]},
        ),
        migrations.CreateModel(
            name="Assignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180, verbose_name="назва")),
                ("task", models.TextField(verbose_name="завдання")),
                ("due_date", models.DateField(blank=True, null=True, verbose_name="дедлайн")),
                ("max_points", models.PositiveIntegerField(default=100, verbose_name="максимум балів")),
                ("lesson", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignments", to="learning.lesson", verbose_name="урок")),
            ],
            options={"verbose_name": "домашнє завдання", "verbose_name_plural": "домашні завдання"},
        ),
        migrations.CreateModel(
            name="Material",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180, verbose_name="назва")),
                ("file", models.FileField(blank=True, upload_to="materials/", verbose_name="файл")),
                ("external_url", models.URLField(blank=True, verbose_name="посилання")),
                ("description", models.TextField(blank=True, verbose_name="опис")),
                ("lesson", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="materials", to="learning.lesson", verbose_name="урок")),
            ],
            options={"verbose_name": "матеріал", "verbose_name_plural": "матеріали"},
        ),
        migrations.CreateModel(
            name="LessonProgress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_done", models.BooleanField(default=False, verbose_name="пройдено")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="оновлено")),
                ("lesson", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="progress", to="learning.lesson", verbose_name="урок")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lesson_progress", to=settings.AUTH_USER_MODEL, verbose_name="учень")),
            ],
            options={"verbose_name": "прогрес уроку", "verbose_name_plural": "прогрес уроків", "unique_together": {("student", "lesson")}},
        ),
        migrations.CreateModel(
            name="Submission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("answer", models.TextField(blank=True, verbose_name="відповідь")),
                ("file", models.FileField(blank=True, upload_to="submissions/", verbose_name="файл роботи")),
                ("submitted_at", models.DateTimeField(auto_now_add=True, verbose_name="здано")),
                ("points", models.PositiveIntegerField(blank=True, null=True, verbose_name="бали")),
                ("teacher_comment", models.TextField(blank=True, verbose_name="коментар викладача")),
                ("assignment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="submissions", to="learning.assignment", verbose_name="завдання")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="submissions", to=settings.AUTH_USER_MODEL, verbose_name="учень")),
            ],
            options={"verbose_name": "здана робота", "verbose_name_plural": "здані роботи", "ordering": ["-submitted_at"]},
        ),
    ]
