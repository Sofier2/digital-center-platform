"""Telegram client and Ukrainian menu for the learning assistant."""

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.utils import timezone

from .models import Assignment, Lesson, LessonProgress, ScheduleEntry, ScheduleException, TelegramAccount


API_URL = "https://api.telegram.org/bot{token}/{method}"
MENU = {
    "keyboard": [["📚 Перелік усіх завдань", "📅 Мій розклад"], ["ℹ️ Допомога"]],
    "resize_keyboard": True,
    "is_persistent": True,
}


def api_call(method, payload=None, timeout=35):
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set.")
    payload = payload or {}
    data = {key: json.dumps(value) if isinstance(value, (dict, list)) else value for key, value in payload.items()}
    request = Request(API_URL.format(token=settings.TELEGRAM_BOT_TOKEN, method=method), data=urlencode(data).encode("utf-8"))
    with urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    if not body.get("ok"):
        raise RuntimeError(body.get("description", "Telegram API error"))
    return body["result"]


def send(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return api_call("sendMessage", payload)


def send_menu(chat_id, text="Оберіть потрібний розділ:"):
    return send(chat_id, text, reply_markup=MENU)


def _link(chat_id, code):
    account = TelegramAccount.objects.select_related("user").filter(link_code=code).first()

    if not account:
        return None, "❌ Код прив’язки не знайдено. Перевірте його в адміністратора."

    # Якщо цей Telegram вже був прив'язаний до іншого користувача,
    # від'єднуємо його.
    TelegramAccount.objects.filter(chat_id=chat_id).exclude(pk=account.pk).update(
        chat_id=None,
        linked_at=None,
    )

    # Переприв'язуємо акаунт
    account.chat_id = chat_id
    account.linked_at = timezone.now()
    account.save(update_fields=["chat_id", "linked_at"])

    return account, "✅ Акаунт успішно підключено."


def _account(chat_id):
    return TelegramAccount.objects.select_related("user").filter(chat_id=chat_id).first()


def _lesson_checklist(user):
    lessons = list(
        Lesson.objects.filter(
            is_available=True,
            module__course__enrollments__student=user,
            module__course__enrollments__is_active=True,
        )
        .select_related("module__course")
        .distinct()
        .order_by("module__course__title", "module__order", "order")
    )
    if not lessons:
        return ["📚 Активних уроків поки немає."]

    done_lesson_ids = set(
        LessonProgress.objects.filter(student=user, is_done=True, lesson_id__in=[lesson.id for lesson in lessons]).values_list("lesson_id", flat=True)
    )
    lessons = [lesson for lesson in lessons if lesson.id not in done_lesson_ids]
    if not lessons:
        return ["✅ Усі уроки позначені як пройдені. Чудова робота!"]

    lines = ["📚 Незроблені завдання", "⬜ — урок ще не позначено як пройдений"]
    current_course = None
    for lesson in lessons:
        course_title = lesson.module.course.title
        if course_title != current_course:
            lines.append(f"\n{course_title}")
            current_course = course_title
        lines.append(f"⬜ Урок {lesson.order}: {lesson.title}\n{settings.PLATFORM_BASE_URL}{lesson.get_absolute_url()}")
    return lines


def _send_lesson_checklist(chat_id, user):
    """Telegram allows up to 4096 characters per message, so split long checklists."""
    chunks, current = [], ""
    for line in _lesson_checklist(user):
        candidate = f"{current}\n\n{line}" if current else line
        if len(candidate) > 3800 and current:
            chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    for index, chunk in enumerate(chunks):
        send(chat_id, chunk, reply_markup=MENU if index == len(chunks) - 1 else None)


def _schedule(user):
    entries = ScheduleEntry.objects.filter(is_cancelled=False, student_id=user.id).order_by("weekday", "starts_at")
    if not entries:
        return f"📅 Розклад ще не призначено. Бот підключено до акаунта «{user.username}». Перевірте, що саме цього учня обрано в полі «Учень» у записі розкладу."
    lines = ["📅 Мій розклад:"]
    for entry in entries:
        duration = f"–{entry.ends_at:%H:%M}" if entry.ends_at else ""
        location = f"\n📍 {entry.location}" if entry.location else ""
        link = f"\n🔗 {entry.meeting_url}" if entry.meeting_url else ""
        lines.append(f"• {entry.get_weekday_display()}, {entry.starts_at:%H:%M}{duration}\n{entry.title}{location}{link}")
    exceptions = ScheduleException.objects.filter(schedule_entry__student_id=user.id, date__gte=timezone.localdate()).select_related("schedule_entry").order_by("date", "starts_at")
    if exceptions:
        lines.append("📌 Зміни на конкретні дати:")
        for item in exceptions:
            title = item.title or item.schedule_entry.title
            if item.is_cancelled:
                lines.append(f"• {item.date:%d.%m.%Y} — {title}: скасовано")
                continue
            starts_at = item.starts_at or item.schedule_entry.starts_at
            location = item.location or item.schedule_entry.location
            meeting_url = item.meeting_url or item.schedule_entry.meeting_url
            location_line = f"\n📍 {location}" if location else ""
            link_line = f"\n🔗 {meeting_url}" if meeting_url else ""
            lines.append(f"• {item.date:%d.%m.%Y}, {starts_at:%H:%M} — {title}{location_line}{link_line}")
    return "\n\n".join(lines)


def send_schedule(user):
    """Send the current weekly schedule to the linked Telegram account."""
    account = TelegramAccount.objects.filter(user=user, chat_id__isnull=False).first()
    if not account:
        return False
    send(account.chat_id, _schedule(user), reply_markup=MENU)
    return True


def notify_new_assignment(assignment, recipient):
    account = TelegramAccount.objects.filter(user=recipient, chat_id__isnull=False).first()
    if not account:
        return False
    deadline = f"\nДедлайн: {assignment.due_date:%d.%m.%Y}" if assignment.due_date else ""
    send(account.chat_id, f"📝 Нове домашнє завдання\n{assignment.title}\n{assignment.lesson.title}{deadline}\n{settings.PLATFORM_BASE_URL}/assignments/{assignment.id}/submit/")
    return True


def respond(message):
    chat_id, text = message["chat"]["id"], message.get("text", "").strip()
    if not text:
        return send_menu(chat_id)
    command, *args = text.split(maxsplit=1)
    command = command.split("@", 1)[0].lower()
    if command == "/start":
        if args:
            account, response = _link(chat_id, args[0])
            return send_menu(chat_id, response) if account else send(chat_id, response)
        return send(chat_id, "Вітаю! Надішліть /start КОД_ПРИВ’ЯЗКИ, щоб підключити акаунт.")
    account = _account(chat_id)
    if not account:
        return send(chat_id, "Спочатку підключіть акаунт: /start КОД_ПРИВ’ЯЗКИ")
    # Match both old and new reply-keyboard labels. Telegram can retain an old
    # keyboard for a user, so checking words is more reliable than exact text.
    normalized = text.casefold()
    if command == "/menu" or "допомог" in normalized or normalized == "help":
        return send_menu(chat_id)
    if command in {"/lessons", "/checklist", "/tasks"} or "урок" in normalized or "перелік" in normalized or normalized in {"lessons", "checklist", "tasks"}:
        return _send_lesson_checklist(chat_id, account.user)
    if command == "/schedule" or "розклад" in normalized or normalized == "schedule":
        return send(chat_id, _schedule(account.user), reply_markup=MENU)
    return send_menu(chat_id, "Оберіть дію кнопкою нижче.")
