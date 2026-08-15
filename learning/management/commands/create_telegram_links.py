from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from learning.models import TelegramAccount


class Command(BaseCommand):
    help = "Create Telegram linking codes for users that do not have one yet."

    def handle(self, *args, **options):
        created = 0
        for user in User.objects.filter(is_active=True):
            _, was_created = TelegramAccount.objects.get_or_create(user=user)
            created += was_created
        self.stdout.write(self.style.SUCCESS(f"Created {created} Telegram linking code(s)."))
