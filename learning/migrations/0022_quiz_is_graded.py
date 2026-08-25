from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("learning", "0021_submission_is_reviewed")]

    operations = [
        migrations.AddField(
            model_name="quiz",
            name="is_graded",
            field=models.BooleanField(default=True, verbose_name="показувати оцінку"),
        ),
    ]
