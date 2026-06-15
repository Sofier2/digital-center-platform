from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("learning", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="оновлено"),
        ),
        migrations.AlterUniqueTogether(
            name="submission",
            unique_together={("assignment", "student")},
        ),
    ]
