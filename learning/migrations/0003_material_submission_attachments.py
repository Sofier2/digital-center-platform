from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("learning", "0002_submission_updated_at_unique"),
    ]

    operations = [
        migrations.CreateModel(
            name="MaterialAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180, verbose_name="назва")),
                ("file", models.FileField(blank=True, upload_to="materials/attachments/", verbose_name="файл або скрін")),
                ("external_url", models.URLField(blank=True, verbose_name="відео або посилання")),
                ("note", models.CharField(blank=True, max_length=220, verbose_name="пояснення")),
                ("order", models.PositiveIntegerField(default=1, verbose_name="порядок")),
                ("material", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="learning.material", verbose_name="матеріал")),
            ],
            options={
                "verbose_name": "вкладення матеріалу",
                "verbose_name_plural": "вкладення матеріалів",
                "ordering": ["material", "order", "title"],
            },
        ),
        migrations.CreateModel(
            name="SubmissionAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(blank=True, max_length=180, verbose_name="назва")),
                ("file", models.FileField(blank=True, upload_to="submissions/attachments/", verbose_name="файл або скрін")),
                ("external_url", models.URLField(blank=True, verbose_name="відео або посилання")),
                ("note", models.CharField(blank=True, max_length=220, verbose_name="пояснення")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="додано")),
                ("submission", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="learning.submission", verbose_name="здана робота")),
            ],
            options={
                "verbose_name": "вкладення роботи",
                "verbose_name_plural": "вкладення робіт",
                "ordering": ["created_at"],
            },
        ),
    ]
