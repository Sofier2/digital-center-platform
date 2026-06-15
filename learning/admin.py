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
    Module,
    Profile,
    Submission,
)


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 1
    fields = ("course", "started_at", "is_active")
    autocomplete_fields = ("course",)


admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [EnrollmentInline]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "child_name", "parent_name", "phone")
    list_filter = ("role",)
    search_fields = ("user__username", "user__first_name", "user__last_name", "child_name", "parent_name", "phone")


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


class AssignmentInline(admin.TabularInline):
    model = Assignment
    extra = 1


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "order", "is_available")
    list_filter = ("is_available", "module__course")
    search_fields = ("title", "summary", "content")
    inlines = [MaterialInline, AssignmentInline]


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "external_url")
    search_fields = ("title", "description")


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


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("assignment", "student", "submitted_at", "points")
    list_filter = ("assignment__lesson__module__course",)
    search_fields = ("student__username", "assignment__title", "answer", "teacher_comment")


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("student", "lesson", "is_done", "updated_at")
    list_filter = ("is_done", "lesson__module__course")
    search_fields = ("student__username", "lesson__title")
