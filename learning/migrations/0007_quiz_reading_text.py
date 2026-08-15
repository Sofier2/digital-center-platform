from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("learning", "0006_quiz_question_context_audio"),
    ]

    operations = [
        migrations.AddField(
            model_name="quiz",
            name="reading_title",
            field=models.CharField(blank=True, max_length=180, verbose_name="заголовок тексту для reading"),
        ),
        migrations.AddField(
            model_name="quiz",
            name="reading_text",
            field=models.TextField(blank=True, verbose_name="спільний текст для reading"),
        ),
    ]
