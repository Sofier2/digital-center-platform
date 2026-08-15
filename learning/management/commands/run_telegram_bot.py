from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from learning.telegram_bot import api_call, respond


class Command(BaseCommand):
    help = "Run the Telegram learning bot using long polling."

    def handle(self, *args, **options):
        try:
            api_call("deleteWebhook", {"drop_pending_updates": "false"})
        except RuntimeError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS("Telegram bot is running."))
        offset = None
        next_reminder_check = timezone.now()
        while True:
            if timezone.now() >= next_reminder_check:
                try:
                    call_command("send_24h_reminders")
                except Exception as exc:  # A reminder failure must not stop the bot.
                    self.stderr.write(f"Reminder check failed: {exc}")
                next_reminder_check = timezone.now() + timedelta(minutes=15)
            payload = {"timeout": 30, "allowed_updates": json_updates()} 
            if offset is not None:
                payload["offset"] = offset
            for update in api_call("getUpdates", payload, timeout=40):
                offset = update["update_id"] + 1
                message = update.get("message")
                if message:
                    try:
                        respond(message)
                    except Exception as exc:  # Keep the bot alive if one message fails.
                        self.stderr.write(f"Update {update['update_id']} failed: {exc}")


def json_updates():
    return '["message"]'
