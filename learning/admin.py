from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import (
    Assignment,
    Course,
    Enrollment,
    Lesson,
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
)


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
    list_display = ("user", "role", "child_name", "parent_name", "phone")
    list_filter = ("role",)
    search_fields = ("user__username", "user__first_name", "user__last_name", "child_name", "parent_name", "phone")


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


class MaterialAttachmentInline(admin.TabularInline):
    model = MaterialAttachment
    extra = 1
    fields = ("title", "file", "external_url", "note", "order")


class AssignmentInline(admin.TabularInline):
    model = Assignment
    extra = 1


class QuizInline(admin.TabularInline):
    model = Quiz
    extra = 1
    fields = ("title", "max_points", "passing_percent", "is_published", "allow_retakes", "order")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "order", "is_available")
    list_filter = ("is_available", "module__course")
    search_fields = ("title", "summary", "content")
    inlines = [MaterialInline, AssignmentInline, QuizInline]


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "external_url")
    search_fields = ("title", "description")
    inlines = [MaterialAttachmentInline]


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


class QuizQuestionInline(admin.StackedInline):
    model = QuizQuestion
    extra = 1
    fields = ("context_text", "audio_file", "audio_url", "text", "explanation", "order", "is_active")


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "max_points", "passing_percent", "is_published", "allow_retakes")
    list_filter = ("is_published", "lesson__module__course")
    search_fields = ("title", "description", "lesson__title")
    inlines = [QuizQuestionInline]


class QuizChoiceInline(admin.TabularInline):
    model = QuizChoice
    extra = 3
    fields = ("text", "is_correct", "order")


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz", "order", "is_active")
    list_filter = ("quiz__lesson__module__course", "is_active")
    search_fields = ("text", "context_text", "quiz__title")
    fieldsets = (
        ("Питання", {"fields": ("quiz", "text", "context_text")}),
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
    fields = ("question", "selected_choice", "is_correct")
    readonly_fields = ("question", "selected_choice", "is_correct")
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
    list_display = ("assignment", "student", "submitted_at", "points")
    list_filter = ("assignment__lesson__module__course",)
    search_fields = ("student__username", "assignment__title", "answer", "teacher_comment")
    inlines = [SubmissionAttachmentInline]


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("student", "lesson", "is_done", "updated_at")
    list_filter = ("is_done", "lesson__module__course")
    search_fields = ("student__username", "lesson__title")
