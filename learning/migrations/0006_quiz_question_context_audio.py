from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("learning", "0005_quizzes"),
    ]

    operations = [
        migrations.AddField(
            model_name="quizquestion",
            name="context_text",
            field=models.TextField(blank=True, verbose_name="текст або уривок до питання"),
        ),
        migrations.AddField(
            model_name="quizquestion",
            name="audio_file",
            field=models.FileField(blank=True, upload_to="quizzes/audio/", verbose_name="аудіо для listening"),
        ),
        migrations.AddField(
            model_name="quizquestion",
            name="audio_url",
            field=models.URLField(blank=True, verbose_name="пряме посилання на аудіо"),
        ),
    ]
