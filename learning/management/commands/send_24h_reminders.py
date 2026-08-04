from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from learning.models import LessonReminder, ScheduleEntry, TelegramAccount
from learning.telegram_bot import send


class Command(BaseCommand):
    help = "Send Telegram reminders 24 and 3 hours before recurring classes."
    REMINDER_HOURS = (24, 3)

    def add_arguments(self, parser):
        parser.add_argument("--window-minutes", type=int, default=30, help="Half-width of each reminder time window; default: 30.")

    def handle(self, *args, **options):
        window = timedelta(minutes=max(1, options["window_minutes"]))
        local_now = timezone.localtime()
        attempted = sent = 0
        for lead_hours in self.REMINDER_HOURS:
            target = local_now + timedelta(hours=lead_hours)
            entries = ScheduleEntry.objects.filter(weekday=target.weekday(), is_cancelled=False).select_related("student").prefetch_related("exceptions")
            for entry in entries:
                exception = next((item for item in entry.exceptions.all() if item.date == target.date()), None)
                if exception and exception.is_cancelled:
                    continue
                start_time = exception.starts_at if exception and exception.starts_at else entry.starts_at
                occurrence = timezone.make_aware(datetime.combine(target.date(), start_time), timezone.get_current_timezone())
                if abs(occurrence - target) > window:
                    continue
                title = exception.title if exception and exception.title else entry.title
                location = exception.location if exception and exception.location else entry.location
                meeting_url = exception.meeting_url if exception and exception.meeting_url else entry.meeting_url
                accounts = TelegramAccount.objects.filter(user_id=entry.student_id, chat_id__isnull=False)
                for account in accounts:
                    reminder, _ = LessonReminder.objects.get_or_create(schedule_entry=entry, recipient=account.user, occurrence_date=target.date(), lead_hours=lead_hours)
                    if reminder.sent_at:
                        continue
                    attempted += 1
                    location_line = f"\n{location}" if location else ""
                    link_line = f"\n{meeting_url}" if meeting_url else ""
                    try:
                        send(account.chat_id, f"⏰ Нагадування: заняття через {lead_hours} год.\n{occurrence:%d.%m.%Y о %H:%M}\n{title}{location_line}{link_line}")
                        reminder.sent_at, reminder.error = timezone.now(), ""
                        sent += 1
                    except Exception as exc:
                        reminder.error = str(exc)[:1000]
                    reminder.save(update_fields=["sent_at", "error"])
        self.stdout.write(self.style.SUCCESS(f"Processed {attempted} reminder(s), sent {sent}."))
