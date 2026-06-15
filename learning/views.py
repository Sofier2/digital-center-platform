from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ReviewSubmissionForm, SubmissionForm
from .models import Assignment, Course, Enrollment, Lesson, LessonProgress, ParentChild, Submission, SubmissionAttachment


def is_platform_manager(user):
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    return getattr(getattr(user, "profile", None), "role", "") == "teacher"


def is_parent(user):
    return getattr(getattr(user, "profile", None), "role", "") == "parent"


def user_has_course_access(user, course):
    if is_platform_manager(user):
        return True
    return Enrollment.objects.filter(student=user, course=course, is_active=True).exists()


@login_required
def dashboard(request):
    if is_platform_manager(request.user):
        return redirect("platform_admin_dashboard")
    if is_parent(request.user):
        return redirect("parent_dashboard")

    enrollments = request.user.enrollments.select_related("course").filter(is_active=True)
    courses = Course.objects.filter(enrollments__student=request.user, enrollments__is_active=True, is_published=True).distinct()
    submissions = request.user.submissions.select_related("assignment", "assignment__lesson").order_by("-submitted_at")[:6]

    return render(
        request,
        "learning/dashboard.html",
        {
            "courses": courses,
            "enrollments": enrollments,
            "submissions": submissions,
        },
    )


@login_required
def parent_dashboard(request):
    if not is_parent(request.user) and not request.user.is_staff:
        return redirect("dashboard")

    child_links = ParentChild.objects.filter(parent=request.user).select_related("child")
    children_data = []
    for link in child_links:
        child = link.child
        enrollments = child.enrollments.select_related("course").filter(is_active=True)
        submissions = child.submissions.select_related("assignment", "assignment__lesson", "assignment__lesson__module__course").prefetch_related("attachments").order_by("-submitted_at")
        lessons_total = Lesson.objects.filter(module__course__enrollments__student=child, module__course__enrollments__is_active=True).distinct().count()
        lessons_done = LessonProgress.objects.filter(student=child, is_done=True, lesson__module__course__enrollments__student=child).distinct().count()
        children_data.append(
            {
                "child": child,
                "enrollments": enrollments,
                "submissions": submissions[:6],
                "pending_count": submissions.filter(points__isnull=True).count(),
                "checked_count": submissions.filter(points__isnull=False).count(),
                "lessons_total": lessons_total,
                "lessons_done": lessons_done,
            }
        )

    return render(request, "learning/parent_dashboard.html", {"children_data": children_data})


@login_required
def course_detail(request, pk):
    course = get_object_or_404(
        Course.objects.prefetch_related("modules__lessons"),
        pk=pk,
        is_published=True,
    )
    if not user_has_course_access(request.user, course):
        return redirect("dashboard")
    progress = {
        item.lesson_id: item.is_done
        for item in LessonProgress.objects.filter(student=request.user, lesson__module__course=course)
    }
    return render(request, "learning/course_detail.html", {"course": course, "progress": progress})


@login_required
def lesson_detail(request, pk):
    lesson = get_object_or_404(
        Lesson.objects.select_related("module", "module__course").prefetch_related("materials__attachments", "assignments"),
        pk=pk,
        is_available=True,
    )
    if not user_has_course_access(request.user, lesson.module.course):
        return redirect("dashboard")
    submissions = {
        item.assignment_id: item
        for item in Submission.objects.prefetch_related("attachments").filter(student=request.user, assignment__lesson=lesson)
    }
    return render(request, "learning/lesson_detail.html", {"lesson": lesson, "submissions": submissions})


@login_required
def submit_assignment(request, pk):
    assignment = get_object_or_404(
        Assignment.objects.select_related("lesson", "lesson__module", "lesson__module__course"),
        pk=pk,
    )
    if not user_has_course_access(request.user, assignment.lesson.module.course):
        return redirect("dashboard")

    submission = Submission.objects.filter(assignment=assignment, student=request.user).first()
    if request.method == "POST":
        form = SubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            result = form.save(commit=False)
            result.assignment = assignment
            result.student = request.user
            result.points = None
            result.teacher_comment = ""
            result.save()
            for uploaded_file in request.FILES.getlist("extra_files"):
                SubmissionAttachment.objects.create(
                    submission=result,
                    title=uploaded_file.name,
                    file=uploaded_file,
                )
            for raw_link in form.cleaned_data.get("extra_links", "").splitlines():
                link = raw_link.strip()
                if link:
                    SubmissionAttachment.objects.create(
                        submission=result,
                        title="Посилання",
                        external_url=link,
                    )
            messages.success(request, "Роботу збережено. Викладач побачить її в кабінеті перевірки.")
            return redirect("lesson_detail", pk=assignment.lesson_id)
    else:
        form = SubmissionForm(instance=submission)

    return render(
        request,
        "learning/submit_assignment.html",
        {"assignment": assignment, "form": form, "submission": submission},
    )


@login_required
@user_passes_test(is_platform_manager)
def platform_admin_dashboard(request):
    submissions = Submission.objects.select_related("student", "assignment", "assignment__lesson").prefetch_related("attachments").order_by("-submitted_at")[:8]
    context = {
        "courses_count": Course.objects.count(),
        "students_count": User.objects.filter(enrollments__isnull=False).distinct().count(),
        "pending_count": Submission.objects.filter(points__isnull=True).count(),
        "checked_count": Submission.objects.filter(points__isnull=False).count(),
        "submissions": submissions,
    }
    return render(request, "learning/platform_admin/dashboard.html", context)


@login_required
@user_passes_test(is_platform_manager)
def platform_admin_courses(request):
    courses = Course.objects.annotate(
        students_total=Count("enrollments", filter=Q(enrollments__is_active=True), distinct=True),
        lessons_total=Count("modules__lessons", distinct=True),
    ).prefetch_related("modules")
    return render(request, "learning/platform_admin/courses.html", {"courses": courses})


@login_required
@user_passes_test(is_platform_manager)
def platform_admin_students(request):
    if request.method == "POST":
        student = get_object_or_404(User, pk=request.POST.get("student_id"))
        course = get_object_or_404(Course, pk=request.POST.get("course_id"))
        action = request.POST.get("action")
        enrollment, _ = Enrollment.objects.get_or_create(
            student=student,
            course=course,
            defaults={"started_at": date.today(), "is_active": True},
        )
        enrollment.is_active = action != "remove"
        enrollment.save()
        if enrollment.is_active:
            messages.success(request, f"Курс '{course.title}' призначено для {student.get_full_name() or student.username}.")
        else:
            messages.success(request, f"Доступ до курсу '{course.title}' знято.")
        return redirect("platform_admin_students")

    students = User.objects.filter(is_staff=False).prefetch_related("enrollments__course", "submissions").order_by("first_name", "last_name", "username")
    all_courses = Course.objects.filter(is_published=True)
    return render(request, "learning/platform_admin/students.html", {"students": students, "all_courses": all_courses})


@login_required
@user_passes_test(is_platform_manager)
def platform_admin_submissions(request):
    status = request.GET.get("status", "pending")
    submissions = Submission.objects.select_related("student", "assignment", "assignment__lesson", "assignment__lesson__module__course").prefetch_related("attachments")
    if status == "checked":
        submissions = submissions.filter(points__isnull=False)
    elif status == "all":
        submissions = submissions.all()
    else:
        submissions = submissions.filter(points__isnull=True)
    return render(request, "learning/platform_admin/submissions.html", {"submissions": submissions, "status": status})


@login_required
@user_passes_test(is_platform_manager)
def review_submission(request, pk):
    submission = get_object_or_404(
        Submission.objects.select_related("student", "assignment", "assignment__lesson", "assignment__lesson__module__course").prefetch_related("attachments"),
        pk=pk,
    )
    if request.method == "POST":
        form = ReviewSubmissionForm(request.POST, instance=submission)
        if form.is_valid():
            form.save()
            messages.success(request, "Оцінку й коментар збережено.")
            return redirect("platform_admin_submissions")
    else:
        form = ReviewSubmissionForm(instance=submission)
    return render(request, "learning/platform_admin/review_submission.html", {"submission": submission, "form": form})
