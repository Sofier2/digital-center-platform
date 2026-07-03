from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import QuizTakeForm, ReviewSubmissionForm, SubmissionForm
from .models import (
    Assignment,
    Course,
    Enrollment,
    Lesson,
    LessonProgress,
    ParentChild,
    Quiz,
    QuizAnswer,
    QuizAttempt,
    Submission,
    SubmissionAttachment,
)


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
        quiz_attempts = child.quiz_attempts.select_related("quiz", "quiz__lesson", "quiz__lesson__module__course").order_by("-completed_at")
        lessons_total = Lesson.objects.filter(module__course__enrollments__student=child, module__course__enrollments__is_active=True).distinct().count()
        lessons_done = LessonProgress.objects.filter(student=child, is_done=True, lesson__module__course__enrollments__student=child).distinct().count()
        children_data.append(
            {
                "child": child,
                "enrollments": enrollments,
                "submissions": submissions[:6],
                "quiz_attempts": quiz_attempts[:6],
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
        Course.objects.prefetch_related("modules__lessons__assignments", "modules__lessons__quizzes"),
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
        Lesson.objects.select_related("module", "module__course").prefetch_related("materials__attachments", "assignments", "quizzes"),
        pk=pk,
        is_available=True,
    )
    if not user_has_course_access(request.user, lesson.module.course):
        return redirect("dashboard")
    submissions = {
        item.assignment_id: item
        for item in Submission.objects.prefetch_related("attachments").filter(student=request.user, assignment__lesson=lesson)
    }
    quiz_attempts = {}
    for item in QuizAttempt.objects.filter(student=request.user, quiz__lesson=lesson).order_by("quiz_id", "-completed_at"):
        quiz_attempts.setdefault(item.quiz_id, item)
    return render(request, "learning/lesson_detail.html", {"lesson": lesson, "submissions": submissions, "quiz_attempts": quiz_attempts})


@login_required
def take_quiz(request, pk):
    quiz = get_object_or_404(
        Quiz.objects.select_related("lesson", "lesson__module", "lesson__module__course").prefetch_related("questions__choices"),
        pk=pk,
        is_published=True,
    )
    if not user_has_course_access(request.user, quiz.lesson.module.course):
        return redirect("dashboard")

    latest_attempt = QuizAttempt.objects.filter(quiz=quiz, student=request.user).order_by("-completed_at").first()
    questions = [question for question in quiz.questions.all() if question.is_active and question.choices.exists()]
    if latest_attempt and not quiz.allow_retakes and request.method != "POST":
        return render(request, "learning/quiz_result.html", {"quiz": quiz, "attempt": latest_attempt})

    if request.method == "POST":
        if latest_attempt and not quiz.allow_retakes:
            return redirect("quiz_result", pk=latest_attempt.pk)
        form = QuizTakeForm(request.POST, questions=questions)
        if form.is_valid():
            correct_count = 0
            selected_by_question = {}
            for question in questions:
                selected_id = int(form.cleaned_data[f"question_{question.id}"])
                selected_choice = next((choice for choice in question.choices.all() if choice.id == selected_id), None)
                selected_by_question[question.id] = selected_choice
                if selected_choice and selected_choice.is_correct:
                    correct_count += 1

            total_count = len(questions)
            score_percent = round((correct_count / total_count) * 100) if total_count else 0
            points = round((correct_count / total_count) * quiz.max_points) if total_count else 0
            attempt = QuizAttempt.objects.create(
                quiz=quiz,
                student=request.user,
                correct_count=correct_count,
                total_count=total_count,
                score_percent=score_percent,
                points=points,
            )
            for question in questions:
                selected_choice = selected_by_question.get(question.id)
                QuizAnswer.objects.create(
                    attempt=attempt,
                    question=question,
                    selected_choice=selected_choice,
                    is_correct=bool(selected_choice and selected_choice.is_correct),
                )
            LessonProgress.objects.update_or_create(
                student=request.user,
                lesson=quiz.lesson,
                defaults={"is_done": True},
            )
            messages.success(request, "Тест завершено. Результат збережено в кабінеті.")
            return redirect("quiz_result", pk=attempt.pk)
    else:
        form = QuizTakeForm(questions=questions)

    question_fields = [
        {"question": question, "field": form[f"question_{question.id}"]}
        for question in questions
    ]
    return render(
        request,
        "learning/take_quiz.html",
        {
            "quiz": quiz,
            "form": form,
            "question_fields": question_fields,
            "questions_count": len(questions),
            "latest_attempt": latest_attempt,
        },
    )


@login_required
def quiz_result(request, pk):
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related("quiz", "quiz__lesson", "quiz__lesson__module", "quiz__lesson__module__course").prefetch_related("answers__question", "answers__selected_choice"),
        pk=pk,
    )
    if attempt.student != request.user and not is_platform_manager(request.user):
        return redirect("dashboard")
    return render(request, "learning/quiz_result.html", {"quiz": attempt.quiz, "attempt": attempt})


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
            LessonProgress.objects.update_or_create(
                student=request.user,
                lesson=assignment.lesson,
                defaults={"is_done": True},
            )
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
    quiz_attempts = QuizAttempt.objects.select_related("student", "quiz", "quiz__lesson").order_by("-completed_at")[:8]
    context = {
        "courses_count": Course.objects.count(),
        "students_count": User.objects.filter(enrollments__isnull=False).distinct().count(),
        "pending_count": Submission.objects.filter(points__isnull=True).count(),
        "checked_count": Submission.objects.filter(points__isnull=False).count(),
        "quiz_attempts_count": QuizAttempt.objects.count(),
        "submissions": submissions,
        "quiz_attempts": quiz_attempts,
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
def platform_admin_quizzes(request):
    attempts = QuizAttempt.objects.select_related("student", "quiz", "quiz__lesson", "quiz__lesson__module__course").order_by("-completed_at")
    return render(request, "learning/platform_admin/quizzes.html", {"attempts": attempts})


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
