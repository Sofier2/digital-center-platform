from django.conf import settings
from django.db import migrations, models
from learning.models import generate_telegram_link_code


class Migration(migrations.Migration):
    dependencies = [
        ("learning", "0010_material_is_code"),
    ]

    operations = [
        migrations.CreateModel(
            name="TelegramAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("chat_id", models.BigIntegerField(blank=True, null=True, unique=True, verbose_name="Telegram chat ID")),
                ("link_code", models.CharField(default=generate_telegram_link_code, editable=False, max_length=32, unique=True, verbose_name="код прив’язки")),
                ("linked_at", models.DateTimeField(blank=True, null=True, verbose_name="прив’язано")),
                ("user", models.OneToOneField(on_delete=models.deletion.CASCADE, related_name="telegram_account", to=settings.AUTH_USER_MODEL, verbose_name="користувач")),
            ],
            options={"verbose_name": "Telegram-акаунт", "verbose_name_plural": "Telegram-акаунти"},
        ),
    ]
