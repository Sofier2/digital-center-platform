from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import (
    Assignment,
    AttendanceRecord,
    AttendanceSession,
    Course,
    Enrollment,
    Lesson,
    LessonStep,
    LessonProgress,
    Material,
    MaterialAttachment,
    Module,
    ParentChild,
    Profile,
    Quiz,
    QuizAnswer,
    QuizAttempt,
    QuizChoice,
    QuizQuestion,
    Submission,
    SubmissionAttachment,
    ScheduleEntry,
    ScheduleException,
    HomeworkNotification,
    LessonReminder,
    StudentWord,
    TelegramAccount,
    TelegramBroadcast,
    VocabularySet,
    VocabularyWord,
)


@admin.action(description="Надіслати актуальний розклад у Telegram")
def send_schedule_to_telegram(modeladmin, request, queryset):
    """One action sends each selected student's full schedule, not one row."""
    from .telegram_bot import send_schedule

    sent = missing = failed = 0
    student_ids = queryset.values_list("student_id", flat=True).distinct()
    for student in User.objects.filter(pk__in=student_ids):
        try:
            if send_schedule(student):
                sent += 1
            else:
                missing += 1
        except Exception:
            failed += 1
    message = f"Розклад надіслано: {sent}. Без прив’язаного Telegram: {missing}. Помилок: {failed}."
    level = messages.SUCCESS if not failed else messages.WARNING
    modeladmin.message_user(request, message, level=level)


@admin.action(description="Надіслати повідомлення про вибрані домашні завдання")
def announce_homework_to_telegram(modeladmin, request, queryset):
    from .signals import deliver_homework_announcement

    for assignment in queryset:
        deliver_homework_announcement(assignment.pk)
    modeladmin.message_user(request, "Повідомлення про домашні завдання надіслано прив'язаним учням.", level=messages.SUCCESS)


@admin.action(description="Надіслати вибрані розсилки в Telegram")
def send_broadcast_to_telegram(modeladmin, request, queryset):
    from django.utils import timezone
    from .telegram_bot import send

    total_sent = total_missing = total_failed = 0
    errors = []
    for broadcast in queryset:
        recipients = broadcast.recipients.all()
        # Include every linked account, including a staff account used for testing.
        accounts = TelegramAccount.objects.filter(chat_id__isnull=False)
        if recipients.exists():
            accounts = accounts.filter(user__in=recipients)
        for account in accounts.select_related("user"):
            try:
                send(account.chat_id, f"📣 {broadcast.title}\n\n{broadcast.message}")
                total_sent += 1
            except Exception as exc:
                total_failed += 1
                errors.append(str(exc))
        total_missing += recipients.exclude(telegram_account__chat_id__isnull=False).count() if recipients.exists() else 0
        broadcast.sent_at = timezone.now()
        broadcast.save(update_fields=["sent_at"])
    level = messages.SUCCESS if not total_failed else messages.WARNING
    detail = f" Причина: {errors[0]}" if errors else ""
    modeladmin.message_user(request, f"Надіслано: {total_sent}. Без Telegram: {total_missing}. Помилок: {total_failed}.{detail}", level=level)


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 1
    fields = ("course", "started_at", "is_active")
    autocomplete_fields = ("course",)


class ParentChildInline(admin.TabularInline):
    model = ParentChild
    fk_name = "parent"
    extra = 1
    fields = ("child", "note")
    autocomplete_fields = ("child",)


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [EnrollmentInline, ParentChildInline]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "child_name", "parent_name", "phone", "learning_goal")
    list_filter = ("role",)
    search_fields = ("user__username", "user__first_name", "user__last_name", "child_name", "parent_name", "phone", "learning_goal")


@admin.register(TelegramAccount)
class TelegramAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "chat_id", "link_code", "linked_at")
    search_fields = ("user__username", "user__first_name", "user__last_name", "link_code")
    readonly_fields = ("link_code", "linked_at")


@admin.register(TelegramBroadcast)
class TelegramBroadcastAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at", "sent_at")
    search_fields = ("title", "message")
    filter_horizontal = ("recipients",)
    actions = [send_broadcast_to_telegram]


@admin.register(ParentChild)
class ParentChildAdmin(admin.ModelAdmin):
    list_display = ("parent", "child", "note", "created_at")
    search_fields = ("parent__username", "parent__first_name", "parent__last_name", "child__username", "child__first_name", "child__last_name")
    autocomplete_fields = ("parent", "child")


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "direction", "age_range", "schedule", "price", "is_published")
    list_filter = ("direction", "is_published")
    search_fields = ("title", "short_description")
    inlines = [ModuleInline]


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)
    search_fields = ("title", "description")
    inlines = [LessonInline]


class MaterialInline(admin.TabularInline):
    model = Material
    extra = 1
    fields = ("title", "description", "is_code", "file", "external_url")


class LessonStepInline(admin.TabularInline):
    model = LessonStep
    extra = 0
    fields = ("kind", "order")
    verbose_name = "крок уроку"
    verbose_name_plural = "Кроки уроку (додайте тільки ті, які мають бачити учні)"


class MaterialAttachmentInline(admin.TabularInline):
    model = MaterialAttachment
    extra = 1
    fields = ("title", "file", "external_url", "note", "order")


class VocabularyWordInline(admin.TabularInline):
    model = VocabularyWord
    extra = 3
    fields = ("word", "translation", "example", "order")


class AssignmentInline(admin.TabularInline):
    model = Assignment
    extra = 1


class QuizInline(admin.TabularInline):
    model = Quiz
    extra = 1
    fields = ("title", "max_points", "passing_percent", "is_published", "allow_retakes", "order")


class VocabularySetInline(admin.TabularInline):
    model = VocabularySet
    extra = 1
    fields = ("title", "description", "order", "is_published")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "order", "is_available")
    list_filter = ("is_available", "module__course")
    search_fields = ("title", "summary", "content")
    inlines = [LessonStepInline, MaterialInline, VocabularySetInline, AssignmentInline, QuizInline]


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "external_url")
    search_fields = ("title", "description")
    fields = ("lesson", "title", "description", "is_code", "file", "external_url")
    inlines = [MaterialAttachmentInline]


@admin.register(VocabularySet)
class VocabularySetAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "order", "is_published")
    list_filter = ("is_published", "lesson__module__course")
    search_fields = ("title", "description", "lesson__title")
    inlines = [VocabularyWordInline]


@admin.register(VocabularyWord)
class VocabularyWordAdmin(admin.ModelAdmin):
    list_display = ("word", "translation", "vocabulary_set", "order")
    list_filter = ("vocabulary_set__lesson__module__course",)
    search_fields = ("word", "translation", "example", "vocabulary_set__title")


@admin.register(StudentWord)
class StudentWordAdmin(admin.ModelAdmin):
    list_display = ("student", "word", "status", "updated_at")
    list_filter = ("status", "word__vocabulary_set__lesson__module__course")
    search_fields = ("student__username", "student__first_name", "student__last_name", "word__word", "word__translation")
    autocomplete_fields = ("student", "word")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "started_at", "is_active")
    list_filter = ("course", "is_active")
    search_fields = ("student__username", "student__first_name", "student__last_name", "course__title")


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "due_date", "max_points")
    list_filter = ("lesson__module__course",)
    search_fields = ("title", "task")
    actions = [announce_homework_to_telegram]


class ScheduleExceptionInline(admin.TabularInline):
    model = ScheduleException
    extra = 0
    fields = ("date", "is_cancelled", "title", "starts_at", "ends_at", "location", "meeting_url", "note")

@admin.register(ScheduleEntry)
class ScheduleEntryAdmin(admin.ModelAdmin):
    list_display = ("student", "title", "weekday", "starts_at", "ends_at", "teacher", "location", "is_cancelled")
    list_filter = ("weekday", "is_cancelled")
    search_fields = ("student__username", "student__first_name", "student__last_name", "title", "teacher", "location")
    autocomplete_fields = ("student",)
    inlines = [ScheduleExceptionInline]
    actions = [send_schedule_to_telegram]


@admin.register(ScheduleException)
class ScheduleExceptionAdmin(admin.ModelAdmin):
    list_display = ("schedule_entry", "date", "is_cancelled", "starts_at", "ends_at")
    list_filter = ("is_cancelled", "date")
    search_fields = ("schedule_entry__student__username", "schedule_entry__title", "title")
    autocomplete_fields = ("schedule_entry",)


@admin.register(HomeworkNotification)
class HomeworkNotificationAdmin(admin.ModelAdmin):
    list_display = ("assignment", "recipient", "sent_at", "error")
    search_fields = ("assignment__title", "recipient__username")
    readonly_fields = ("assignment", "recipient", "sent_at", "error")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(LessonReminder)
class LessonReminderAdmin(admin.ModelAdmin):
    list_display = ("schedule_entry", "recipient", "occurrence_date", "lead_hours", "sent_at", "error")
    search_fields = ("schedule_entry__student__username", "schedule_entry__title", "recipient__username")
    readonly_fields = ("schedule_entry", "recipient", "occurrence_date", "lead_hours", "sent_at", "error")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class QuizQuestionInline(admin.StackedInline):
    model = QuizQuestion
    extra = 1
    fields = ("question_type", "text", "correct_answer", "drag_options", "context_text", "image_file", "image_url", "audio_file", "audio_url", "explanation", "order", "is_active")


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "max_points", "passing_percent", "is_published", "allow_retakes")
    list_filter = ("is_published", "lesson__module__course")
    search_fields = ("title", "description", "reading_title", "reading_text", "lesson__title")
    fieldsets = (
        ("Основне", {"fields": ("lesson", "title", "description")}),
        ("Reading", {"fields": ("reading_title", "reading_text"), "description": "Додай один великий текст, який учень читатиме під час усього тесту."}),
        ("Оцінювання", {"fields": ("max_points", "passing_percent", "allow_retakes")}),
        ("Публікація", {"fields": ("is_published", "order")}),
    )
    inlines = [QuizQuestionInline]


class QuizChoiceInline(admin.TabularInline):
    model = QuizChoice
    extra = 3
    fields = ("text", "is_correct", "order")


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    fields = ("student", "status", "note")
    autocomplete_fields = ("student",)


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ("course", "date", "title")
    list_filter = ("course", "date")
    search_fields = ("course__title", "title")
    inlines = [AttendanceRecordInline]


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "session", "status", "note")
    list_filter = ("status", "session__course", "session__date")
    search_fields = ("student__username", "student__first_name", "student__last_name", "note")


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "question_type", "quiz", "order", "is_active")
    list_filter = ("quiz__lesson__module__course", "is_active")
    search_fields = ("text", "context_text", "quiz__title")
    fieldsets = (
        ("Питання", {"fields": ("quiz", "question_type", "text", "correct_answer", "drag_options", "context_text"), "description": "Для текстового типу заповніть правильну відповідь. Для перетягування додайте варіанти, кожен з нового рядка; у тексті питання можна використати ___ для пропуску."}),
        ("Зображення", {"fields": ("image_file", "image_url"), "description": "Завантажте зображення або вставте пряме посилання на нього."}),
        ("Listening", {"fields": ("audio_file", "audio_url"), "description": "Завантаж аудіофайл або встав пряме посилання на MP3/M4A/WAV."}),
        ("Після відповіді", {"fields": ("explanation",)}),
        ("Налаштування", {"fields": ("order", "is_active")}),
    )
    inlines = [QuizChoiceInline]


@admin.register(QuizChoice)
class QuizChoiceAdmin(admin.ModelAdmin):
    list_display = ("text", "question", "is_correct", "order")
    list_filter = ("is_correct", "question__quiz")
    search_fields = ("text", "question__text")


class QuizAnswerInline(admin.TabularInline):
    model = QuizAnswer
    extra = 0
    fields = ("question", "selected_choice", "text_answer", "is_correct")
    readonly_fields = ("question", "selected_choice", "text_answer", "is_correct")
    can_delete = False


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("quiz", "student", "score_percent", "points", "correct_count", "total_count", "completed_at")
    list_filter = ("quiz__lesson__module__course", "quiz")
    search_fields = ("student__username", "student__first_name", "student__last_name", "quiz__title")
    readonly_fields = ("quiz", "student", "correct_count", "total_count", "score_percent", "points", "started_at", "completed_at")
    inlines = [QuizAnswerInline]


class SubmissionAttachmentInline(admin.TabularInline):
    model = SubmissionAttachment
    extra = 0
    fields = ("title", "file", "external_url", "note", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("assignment", "student", "submitted_at", "is_reviewed", "points")
    list_filter = ("assignment__lesson__module__course",)
    search_fields = ("student__username", "assignment__title", "answer", "teacher_comment")
    inlines = [SubmissionAttachmentInline]


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("student", "lesson", "is_done", "updated_at")
    list_filter = ("is_done", "lesson__module__course")
    search_fields = ("student__username", "lesson__title")
