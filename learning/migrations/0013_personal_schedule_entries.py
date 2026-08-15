from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def move_course_entries_to_students(apps, schema_editor):
    ScheduleEntry = apps.get_model("learning", "ScheduleEntry")
    Enrollment = apps.get_model("learning", "Enrollment")
    for entry in ScheduleEntry.objects.all().iterator():
        student_ids = list(Enrollment.objects.filter(course_id=entry.course_id, is_active=True).values_list("student_id", flat=True))
        if not student_ids:
            entry.delete()
            continue
        entry.student_id = student_ids[0]
        entry.save(update_fields=["student"])
        for student_id in student_ids[1:]:
            ScheduleEntry.objects.create(
                course_id=entry.course_id,
                lesson_id=entry.lesson_id,
                student_id=student_id,
                title=entry.title,
                starts_at=entry.starts_at,
                ends_at=entry.ends_at,
                teacher=entry.teacher,
                location=entry.location,
                meeting_url=entry.meeting_url,
                note=entry.note,
                is_cancelled=entry.is_cancelled,
                created_at=entry.created_at,
            )


class Migration(migrations.Migration):
    dependencies = [("learning", "0012_scheduleentry_homeworknotification_lessonreminder")]

    operations = [
        migrations.AddField(
            model_name="scheduleentry",
            name="student",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="schedule_entries", to=settings.AUTH_USER_MODEL, verbose_name="учень"),
        ),
        migrations.AddField(
            model_name="scheduleentry",
            name="title",
            field=models.CharField(default="Заняття", max_length=180, verbose_name="назва заняття"),
            preserve_default=False,
        ),
        migrations.RunPython(move_course_entries_to_students, migrations.RunPython.noop),
        migrations.RemoveField(model_name="scheduleentry", name="course"),
        migrations.RemoveField(model_name="scheduleentry", name="lesson"),
        migrations.AlterField(
            model_name="scheduleentry",
            name="student",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="schedule_entries", to=settings.AUTH_USER_MODEL, verbose_name="учень"),
        ),
    ]
