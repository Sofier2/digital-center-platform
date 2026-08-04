from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ProfileForm, QuizTakeForm, ReviewSubmissionForm, SubmissionForm
from .models import (
    Assignment,
    AttendanceRecord,
    AttendanceSession,
    Course,
    Enrollment,
    Lesson,
    LessonProgress,
    ParentChild,
    Profile,
    Quiz,
    QuizAnswer,
    QuizAttempt,
    QuizChoice,
    QuizQuestion,
    StudentWord,
    Submission,
    SubmissionAttachment,
    ScheduleEntry,
    ScheduleException,
    VocabularyWord,
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
    profile, _ = Profile.objects.get_or_create(user=request.user)
    words_to_learn = (
        request.user.word_progress.select_related(
            "word",
            "word__vocabulary_set",
            "word__vocabulary_set__lesson",
            "word__vocabulary_set__lesson__module",
            "word__vocabulary_set__lesson__module__course",
        )
        .filter(status__in=[StudentWord.Status.UNKNOWN, StudentWord.Status.LEARNING])
        .order_by("-updated_at")[:8]
    )
    lessons_total = Lesson.objects.filter(module__course__in=courses).distinct().count()
    lessons_done = LessonProgress.objects.filter(student=request.user, is_done=True, lesson__module__course__in=courses).distinct().count()

    return render(
        request,
        "learning/dashboard.html",
        {
            "courses": courses,
            "enrollments": enrollments,
            "submissions": submissions,
            "profile": profile,
            "words_to_learn": words_to_learn,
            "unknown_words_count": request.user.word_progress.filter(status=StudentWord.Status.UNKNOWN).count(),
            "learning_words_count": request.user.word_progress.filter(status=StudentWord.Status.LEARNING).count(),
            "lessons_total": lessons_total,
            "lessons_done": lessons_done,
        },
    )


@login_required
def schedule(request):
    """Show only meetings the current user is entitled to see."""
    entries = ScheduleEntry.objects.select_related("student").filter(is_cancelled=False)
    if is_platform_manager(request.user):
        pass
    elif is_parent(request.user):
        child_ids = ParentChild.objects.filter(parent=request.user).values_list("child_id", flat=True)
        entries = entries.filter(student_id__in=child_ids)
    else:
        entries = entries.filter(student=request.user)
    entries = entries.distinct().order_by("weekday", "starts_at")
    exceptions = ScheduleException.objects.filter(schedule_entry__in=entries, date__gte=timezone.localdate()).select_related("schedule_entry").order_by("date", "starts_at")
    return render(request, "learning/schedule.html", {"entries": entries, "exceptions": exceptions})


@login_required
def my_attendance(request):
    if is_platform_manager(request.user):
        return redirect("platform_admin_attendance")
    records = (
        AttendanceRecord.objects.filter(student=request.user)
        .select_related("session", "session__course")
        .order_by("-session__date", "session__course__title")
    )
    return render(request, "learning/my_attendance.html", {"records": records})


@login_required
def profile_settings(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Профіль оновлено.")
            return redirect("dashboard")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "learning/profile_settings.html", {"form": form, "profile": profile})


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
        Lesson.objects.select_related("module", "module__course").prefetch_related("steps", "materials__attachments", "vocabulary_sets__words", "assignments", "quizzes"),
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
    word_statuses = {
        item.word_id: item.status
        for item in StudentWord.objects.filter(student=request.user, word__vocabulary_set__lesson=lesson)
    }
    steps = list(lesson.steps.all())
    if not steps:
        # Lessons created before the step constructor keep their familiar full layout.
        steps = [
            {"kind": "topic", "get_kind_display": "Тема уроку", "order": 1},
            {"kind": "materials", "get_kind_display": "Матеріали", "order": 2},
            {"kind": "vocabulary", "get_kind_display": "Слова", "order": 3},
            {"kind": "homework", "get_kind_display": "Домашнє завдання", "order": 4},
            {"kind": "quiz", "get_kind_display": "Тест", "order": 5},
        ]
    return render(
        request,
        "learning/lesson_detail.html",
        {
            "lesson": lesson,
            "submissions": submissions,
            "quiz_attempts": quiz_attempts,
            "word_statuses": word_statuses,
            "steps": steps,
        },
    )


@login_required
def update_word_status(request, pk):
    word = get_object_or_404(
        VocabularyWord.objects.select_related("vocabulary_set", "vocabulary_set__lesson", "vocabulary_set__lesson__module", "vocabulary_set__lesson__module__course"),
        pk=pk,
    )
    lesson = word.vocabulary_set.lesson
    if not user_has_course_access(request.user, lesson.module.course):
        return redirect("dashboard")
    if request.method == "POST":
        status = request.POST.get("status")
        if status in StudentWord.Status.values:
            StudentWord.objects.update_or_create(
                student=request.user,
                word=word,
                defaults={"status": status},
            )
            messages.success(request, "Слово збережено у твоєму словнику.")
    return redirect(f"{lesson.get_absolute_url()}#words")


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
    quizzes = Quiz.objects.select_related("lesson", "lesson__module", "lesson__module__course").annotate(questions_total=Count("questions")).order_by("-id")
    return render(request, "learning/platform_admin/quizzes.html", {"attempts": attempts, "quizzes": quizzes})


@login_required
@user_passes_test(is_platform_manager)
def create_quiz(request):
    lessons = Lesson.objects.select_related("module", "module__course").order_by("module__course__title", "module__order", "order")
    if request.method == "POST":
        lesson = get_object_or_404(Lesson, pk=request.POST.get("lesson_id"))
        title = request.POST.get("title", "").strip()
        question_texts = request.POST.getlist("question_text")
        if not title or not any(item.strip() for item in question_texts):
            messages.error(request, "Вкажіть назву тесту та хоча б одне питання.")
        else:
            with transaction.atomic():
                quiz = Quiz.objects.create(
                    lesson=lesson,
                    title=title,
                    description=request.POST.get("description", "").strip(),
                    max_points=request.POST.get("max_points") or 100,
                    passing_percent=request.POST.get("passing_percent") or 60,
                    is_published=request.POST.get("is_published") == "on",
                    allow_retakes=request.POST.get("allow_retakes") == "on",
                )
                created = 0
                for index, text in enumerate(question_texts):
                    text = text.strip()
                    choices = [item.strip() for item in request.POST.getlist(f"choices_{index}") if item.strip()]
                    correct = request.POST.get(f"correct_{index}", "0")
                    if not text or len(choices) < 2:
                        continue
                    question = QuizQuestion.objects.create(quiz=quiz, text=text, order=created + 1)
                    for choice_index, choice in enumerate(choices):
                        QuizChoice.objects.create(question=question, text=choice, order=choice_index + 1, is_correct=str(choice_index) == correct)
                    created += 1
                if not created:
                    quiz.delete()
                    messages.error(request, "Кожне питання має містити щонайменше два варіанти відповіді.")
                else:
                    messages.success(request, f"Тест «{quiz.title}» створено: {created} питань.")
                    return redirect("platform_admin_quizzes")
    return render(request, "learning/platform_admin/create_quiz.html", {"lessons": lessons})


@login_required
@user_passes_test(is_platform_manager)
def platform_admin_attendance(request):
    courses = Course.objects.filter(is_published=True).order_by("title")
    if request.method == "POST":
        course = get_object_or_404(Course, pk=request.POST.get("course_id"))
        session_date = request.POST.get("date") or date.today().isoformat()
        session, created = AttendanceSession.objects.get_or_create(
            course=course, date=session_date,
            defaults={"title": request.POST.get("title", "").strip()},
        )
        if not created and request.POST.get("title", "").strip():
            session.title = request.POST["title"].strip()
            session.save(update_fields=["title"])
        return redirect("edit_attendance", pk=session.pk)
    sessions = AttendanceSession.objects.select_related("course").annotate(students_total=Count("records")).all()
    return render(request, "learning/platform_admin/attendance.html", {"courses": courses, "sessions": sessions, "today": date.today()})


@login_required
@user_passes_test(is_platform_manager)
def edit_attendance(request, pk):
    session = get_object_or_404(AttendanceSession.objects.select_related("course"), pk=pk)
    students = User.objects.filter(enrollments__course=session.course, enrollments__is_active=True).distinct().order_by("first_name", "last_name", "username")
    existing = {record.student_id: record for record in session.records.filter(student__in=students)}
    if request.method == "POST":
        for student in students:
            AttendanceRecord.objects.update_or_create(
                session=session,
                student=student,
                defaults={"status": request.POST.get(f"status_{student.id}", AttendanceRecord.Status.PRESENT), "note": request.POST.get(f"note_{student.id}", "").strip()},
            )
        messages.success(request, "Відвідуваність збережено.")
        return redirect("edit_attendance", pk=session.pk)
    return render(request, "learning/platform_admin/edit_attendance.html", {"session": session, "students": students, "existing": existing, "statuses": AttendanceRecord.Status.choices})


@login_required
@user_passes_test(is_platform_manager)
def delete_attendance(request, pk):
    if request.method != "POST":
        return redirect("platform_admin_attendance")
    session = get_object_or_404(AttendanceSession, pk=pk)
    session.delete()
    messages.success(request, "Запис заняття та його відмітки видалено.")
    return redirect("platform_admin_attendance")


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
