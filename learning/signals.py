"""Domain events that send Telegram updates after a successful database commit."""

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Assignment, HomeworkNotification, TelegramAccount


@receiver(post_save, sender=Assignment)
def announce_new_assignment(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(lambda: deliver_homework_announcement(instance.pk))


def deliver_homework_announcement(assignment_id):
    from .telegram_bot import notify_new_assignment

    assignment = Assignment.objects.select_related("lesson__module__course").get(pk=assignment_id)
    student_ids = assignment.lesson.module.course.enrollments.filter(is_active=True).values_list("student_id", flat=True)
    linked_ids = TelegramAccount.objects.filter(user_id__in=student_ids, chat_id__isnull=False).values_list("user_id", flat=True)
    for user_id in linked_ids:
        delivery, created = HomeworkNotification.objects.get_or_create(assignment=assignment, recipient_id=user_id)
        if delivery.sent_at:
            continue
        try:
            notify_new_assignment(assignment, delivery.recipient)
            delivery.sent_at, delivery.error = timezone.now(), ""
        except Exception as exc:
            delivery.error = str(exc)[:1000]
        delivery.save(update_fields=["sent_at", "error"])
