from django.db import migrations, models


def mark_scored_submissions_reviewed(apps, schema_editor):
    Submission = apps.get_model("learning", "Submission")
    Submission.objects.filter(points__isnull=False).update(is_reviewed=True)


class Migration(migrations.Migration):
    dependencies = [("learning", "0020_quiz_drag_and_images")]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="is_reviewed",
            field=models.BooleanField(default=False, verbose_name="перевірено"),
        ),
        migrations.RunPython(mark_scored_submissions_reviewed, migrations.RunPython.noop),
    ]
