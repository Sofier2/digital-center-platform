import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a superuser from environment variables if it does not exist."

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if not username or not password:
            self.stdout.write("Superuser env vars are not set, skipping.")
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )

        changed = False
        if not user.is_staff or not user.is_superuser:
            user.is_staff = True
            user.is_superuser = True
            changed = True
        if email and user.email != email:
            user.email = email
            changed = True
        if created:
            user.set_password(password)
            changed = True

        if changed:
            user.save()

        status = "created" if created else "already exists"
        self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' {status}."))
