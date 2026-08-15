from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("learning", "0014_weekly_personal_schedule")]

    operations = [
        migrations.CreateModel(
            name="ScheduleException",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(verbose_name="дата")),
                ("title", models.CharField(blank=True, max_length=180, verbose_name="інша назва заняття")),
                ("starts_at", models.TimeField(blank=True, null=True, verbose_name="інший час початку")),
                ("ends_at", models.TimeField(blank=True, null=True, verbose_name="інший час завершення")),
                ("location", models.CharField(blank=True, max_length=180, verbose_name="інше місце або аудиторія")),
                ("meeting_url", models.URLField(blank=True, verbose_name="інше посилання на онлайн-зустріч")),
                ("note", models.TextField(blank=True, verbose_name="примітка")),
                ("is_cancelled", models.BooleanField(default=False, verbose_name="скасувати заняття цього дня")),
                ("schedule_entry", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="exceptions", to="learning.scheduleentry", verbose_name="заняття розкладу")),
            ],
            options={"verbose_name": "зміна розкладу на дату", "verbose_name_plural": "зміни розкладу на окремі дати", "ordering": ["date"]},
        ),
        migrations.RemoveConstraint(model_name="lessonreminder", name="unique_schedule_reminder"),
        migrations.AddField(
            model_name="lessonreminder",
            name="lead_hours",
            field=models.PositiveSmallIntegerField(default=24, verbose_name="годин до заняття"),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name="scheduleexception",
            constraint=models.UniqueConstraint(fields=("schedule_entry", "date"), name="unique_schedule_exception_date"),
        ),
        migrations.AddConstraint(
            model_name="lessonreminder",
            constraint=models.UniqueConstraint(fields=("schedule_entry", "recipient", "occurrence_date", "lead_hours"), name="unique_schedule_reminder"),
        ),
    ]
