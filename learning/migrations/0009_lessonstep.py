from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("learning", "0008_profile_avatar_vocabulary"),
    ]

    operations = [
        migrations.CreateModel(
            name="LessonStep",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("topic", "Тема уроку"), ("materials", "Матеріали"), ("vocabulary", "Слова"), ("homework", "Домашнє завдання"), ("quiz", "Тест")], max_length=20, verbose_name="тип кроку")),
                ("order", models.PositiveIntegerField(default=1, verbose_name="порядок")),
                ("lesson", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="steps", to="learning.lesson", verbose_name="урок")),
            ],
            options={"verbose_name": "крок уроку", "verbose_name_plural": "кроки уроку", "ordering": ["lesson", "order", "id"]},
        ),
        migrations.AddConstraint(
            model_name="lessonstep",
            constraint=models.UniqueConstraint(fields=("lesson", "kind"), name="unique_lesson_step_kind"),
        ),
    ]
