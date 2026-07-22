"""Small Telegram client and the commands used by the learning assistant."""

import json
from datetime import date
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.utils import timezone

from .models import Assignment, Enrollment, Lesson, Submission, TelegramAccount


API_URL = "https://api.telegram.org/bot{token}/{method}"


def api_call(method, payload=None, timeout=35):
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set.")
    data = urlencode(payload or {}).encode("utf-8")
    request = Request(
        API_URL.format(token=settings.TELEGRAM_BOT_TOKEN, method=method), data=data,
    )
    with urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    if not body.get("ok"):
        raise RuntimeError(body.get("description", "Telegram API error"))
    return body["result"]


def send(chat_id, text):
    return api_call("sendMessage", {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"})


def _name(user):
    return user.get_full_name() or user.username


def _link(chat_id, code):
    account = TelegramAccount.objects.select_related("user").filter(link_code=code).first()
    if not account:
        return "Не знайшов код прив’язки. Перевір його в кабінеті адміністратора."
    if account.chat_id and account.chat_id != chat_id:
        return "Цей код уже використано. Попросіть викладача створити новий код."
    account.chat_id = chat_id
    account.linked_at = timezone.now()
    account.save(update_fields=["chat_id", "linked_at"])
    return f"Готово, {_name(account.user)}! Тепер доступні /lessons і /homework."


def _account(chat_id):
    return TelegramAccount.objects.select_related("user").filter(chat_id=chat_id).first()


def _lessons(user):
    lessons = Lesson.objects.filter(
        is_available=True,
        module__course__enrollments__student=user,
        module__course__enrollments__is_active=True,
    ).select_related("module__course").distinct().order_by("module__course__title", "module__order", "order")
    if not lessons:
        return "Активних уроків поки немає."
    lines = ["📚 Твої уроки:"]
    for lesson in lessons[:12]:
        url = f"{settings.PLATFORM_BASE_URL}{lesson.get_absolute_url()}"
        lines.append(f"• {lesson.module.course.title}: {lesson.title}\n{url}")
    return "\n\n".join(lines)


def _homework(user):
    submitted_ids = Submission.objects.filter(student=user).values_list("assignment_id", flat=True)
    tasks = Assignment.objects.filter(
        lesson__is_available=True,
        lesson__module__course__enrollments__student=user,
        lesson__module__course__enrollments__is_active=True,
    ).exclude(id__in=submitted_ids).select_related("lesson__module__course").distinct().order_by("due_date", "id")
    if not tasks:
        return "✅ Немає незданих домашніх завдань."
    lines = ["📝 Нездана домашка:"]
    for task in tasks[:12]:
        deadline = f" · до {task.due_date:%d.%m}" if task.due_date else ""
        url = f"{settings.PLATFORM_BASE_URL}/assignments/{task.id}/submit/"
        lines.append(f"• {task.title}{deadline}\n{url}")
    return "\n\n".join(lines)


def respond(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()
    command, *args = text.split(maxsplit=1)
    command = command.split("@", 1)[0].lower()
    if command == "/start":
        if args:
            return send(chat_id, _link(chat_id, args[0]))
        return send(chat_id, "Вітаю! Надішліть /start КОД_ПРИВ’ЯЗКИ, щоб підключити свій акаунт.")
    account = _account(chat_id)
    if not account:
        return send(chat_id, "Спочатку підключіть акаунт: /start КОД_ПРИВ’ЯЗКИ")
    if command == "/lessons":
        return send(chat_id, _lessons(account.user))
    if command == "/homework":
        return send(chat_id, _homework(account.user))
    return send(chat_id, "Команди:\n/lessons — мої уроки\n/homework — нездана домашка")
