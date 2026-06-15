from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import Course, Lesson


@login_required
def dashboard(request):
    enrollments = request.user.enrollments.select_related("course").filter(is_active=True)
    courses = Course.objects.filter(is_published=True)

    if enrollments.exists():
        courses = Course.objects.filter(enrollments__student=request.user, enrollments__is_active=True).distinct()

    return render(
        request,
        "learning/dashboard.html",
        {
            "courses": courses,
            "enrollments": enrollments,
        },
    )


@login_required
def course_detail(request, pk):
    course = get_object_or_404(
        Course.objects.prefetch_related("modules__lessons"),
        pk=pk,
        is_published=True,
    )
    return render(request, "learning/course_detail.html", {"course": course})


@login_required
def lesson_detail(request, pk):
    lesson = get_object_or_404(
        Lesson.objects.select_related("module", "module__course").prefetch_related("materials", "assignments"),
        pk=pk,
        is_available=True,
    )
    return render(request, "learning/lesson_detail.html", {"lesson": lesson})
