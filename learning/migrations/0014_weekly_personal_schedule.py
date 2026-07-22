from django.db import migrations, models
from django.utils import timezone


def convert_to_weekly_schedule(apps, schema_editor):
    ScheduleEntry = apps.get_model("learning", "ScheduleEntry")
    LessonReminder = apps.get_model("learning", "LessonReminder")
    # Clear inherited model ordering: migration 0013 removed ``course``, while
    # the historical ordering still mentioned it on databases upgraded in place.
    for entry in ScheduleEntry.objects.order_by().iterator():
        entry.weekday = entry.starts_at.weekday()
        entry.start_time = entry.starts_at.timetz().replace(tzinfo=None)
        entry.end_time = entry.ends_at.timetz().replace(tzinfo=None) if entry.ends_at else None
        entry.save(update_fields=["weekday", "start_time", "end_time"])
    for reminder in LessonReminder.objects.filter(occurrence_date__isnull=True).iterator():
        reminder.occurrence_date = timezone.localdate(reminder.sent_at) if reminder.sent_at else timezone.localdate()
        reminder.save(update_fields=["occurrence_date"])


class Migration(migrations.Migration):
    dependencies = [("learning", "0013_personal_schedule_entries")]

    operations = [
        migrations.RemoveConstraint(model_name="lessonreminder", name="unique_schedule_reminder"),
        migrations.AddField(
            model_name="scheduleentry",
            name="weekday",
            field=models.PositiveSmallIntegerField(choices=[(0, "Понеділок"), (1, "Вівторок"), (2, "Середа"), (3, "Четвер"), (4, "П’ятниця"), (5, "Субота"), (6, "Неділя")], default=0, verbose_name="день тижня"),
        ),
        migrations.AddField(
            model_name="scheduleentry",
            name="start_time",
            field=models.TimeField(blank=True, null=True, verbose_name="час початку"),
        ),
        migrations.AddField(
            model_name="scheduleentry",
            name="end_time",
            field=models.TimeField(blank=True, null=True, verbose_name="час завершення"),
        ),
        migrations.AddField(
            model_name="lessonreminder",
            name="occurrence_date",
            field=models.DateField(blank=True, null=True, verbose_name="дата заняття"),
        ),
        migrations.RunPython(convert_to_weekly_schedule, migrations.RunPython.noop),
        migrations.RemoveField(model_name="scheduleentry", name="starts_at"),
        migrations.RemoveField(model_name="scheduleentry", name="ends_at"),
        migrations.RenameField(model_name="scheduleentry", old_name="start_time", new_name="starts_at"),
        migrations.RenameField(model_name="scheduleentry", old_name="end_time", new_name="ends_at"),
        migrations.AlterField(
            model_name="scheduleentry",
            name="starts_at",
            field=models.TimeField(verbose_name="час початку"),
        ),
        migrations.AlterField(
            model_name="lessonreminder",
            name="occurrence_date",
            field=models.DateField(verbose_name="дата заняття"),
        ),
        migrations.AlterModelOptions(
            name="scheduleentry",
            options={"ordering": ["student__last_name", "student__first_name", "weekday", "starts_at"], "verbose_name": "заняття в розкладі", "verbose_name_plural": "розклад занять"},
        ),
        migrations.AddConstraint(
            model_name="lessonreminder",
            constraint=models.UniqueConstraint(fields=("schedule_entry", "recipient", "occurrence_date"), name="unique_schedule_reminder"),
        ),
    ]
