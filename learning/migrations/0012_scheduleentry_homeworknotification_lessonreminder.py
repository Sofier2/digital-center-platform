from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("learning", "0011_telegramaccount"),
    ]

    operations = [
        migrations.CreateModel(
            name="ScheduleEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("starts_at", models.DateTimeField(verbose_name="початок заняття")),
                ("ends_at", models.DateTimeField(blank=True, null=True, verbose_name="кінець заняття")),
                ("teacher", models.CharField(blank=True, max_length=140, verbose_name="викладач")),
                ("location", models.CharField(blank=True, max_length=180, verbose_name="місце або аудиторія")),
                ("meeting_url", models.URLField(blank=True, verbose_name="посилання на онлайн-зустріч")),
                ("note", models.TextField(blank=True, verbose_name="примітка")),
                ("is_cancelled", models.BooleanField(default=False, verbose_name="скасовано")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="створено")),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="schedule_entries", to="learning.course", verbose_name="курс")),
                ("lesson", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="schedule_entries", to="learning.lesson", verbose_name="урок")),
            ],
            options={"verbose_name": "заняття в розкладі", "verbose_name_plural": "розклад занять", "ordering": ["starts_at", "course__title"]},
        ),
        migrations.CreateModel(
            name="HomeworkNotification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sent_at", models.DateTimeField(blank=True, null=True, verbose_name="надіслано")),
                ("error", models.TextField(blank=True, verbose_name="помилка")),
                ("assignment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="telegram_notifications", to="learning.assignment")),
                ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="homework_notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "сповіщення про домашнє завдання", "verbose_name_plural": "сповіщення про домашні завдання"},
        ),
        migrations.CreateModel(
            name="LessonReminder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sent_at", models.DateTimeField(blank=True, null=True, verbose_name="надіслано")),
                ("error", models.TextField(blank=True, verbose_name="помилка")),
                ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lesson_reminders", to=settings.AUTH_USER_MODEL)),
                ("schedule_entry", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reminders", to="learning.scheduleentry")),
            ],
            options={"verbose_name": "нагадування про заняття", "verbose_name_plural": "нагадування про заняття"},
        ),
        migrations.AddConstraint(
            model_name="homeworknotification",
            constraint=models.UniqueConstraint(fields=("assignment", "recipient"), name="unique_homework_notification"),
        ),
        migrations.AddConstraint(
            model_name="lessonreminder",
            constraint=models.UniqueConstraint(fields=("schedule_entry", "recipient"), name="unique_schedule_reminder"),
        ),
    ]
