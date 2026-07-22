from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("learning", "0015_scheduleexception_and_reminder_lead_hours")]

    operations = [
        migrations.CreateModel(
            name="TelegramBroadcast",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180, verbose_name="назва розсилки")),
                ("message", models.TextField(verbose_name="текст повідомлення")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="створено")),
                ("sent_at", models.DateTimeField(blank=True, null=True, verbose_name="останнє надсилання")),
                ("recipients", models.ManyToManyField(blank=True, related_name="telegram_broadcasts", to=settings.AUTH_USER_MODEL, verbose_name="одержувачі")),
            ],
            options={"verbose_name": "розсилка Telegram", "verbose_name_plural": "розсилки Telegram", "ordering": ["-created_at"]},
        ),
    ]
