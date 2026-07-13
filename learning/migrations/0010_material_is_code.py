from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("learning", "0009_lessonstep"),
    ]

    operations = [
        migrations.AddField(
            model_name="material",
            name="is_code",
            field=models.BooleanField(default=False, verbose_name="це код — показати кнопку «Скопіювати код»"),
        ),
    ]
