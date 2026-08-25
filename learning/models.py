from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
import secrets


def generate_telegram_link_code():
    return secrets.token_urlsafe(18)


class Profile(models.Model):
    class Role(models.TextChoices):
        STUDENT = "student", "Учень"
        PARENT = "parent", "Батьки"
        TEACHER = "teacher", "Викладач"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField("роль", max_length=20, choices=Role.choices, default=Role.STUDENT)
    phone = models.CharField("телефон", max_length=32, blank=True)
    child_name = models.CharField("ім'я дитини", max_length=120, blank=True)
    parent_name = models.CharField("ім'я одного з батьків", max_length=120, blank=True)
    birth_date = models.DateField("дата народження", blank=True, null=True)
    avatar = models.ImageField("аватар", upload_to="avatars/", blank=True)
    learning_goal = models.CharField("ціль навчання", max_length=180, blank=True)
    notes = models.TextField("нотатки", blank=True)

    class Meta:
        verbose_name = "профіль"
        verbose_name_plural = "профілі"

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class TelegramAccount(models.Model):
    """A private link between a platform user and a Telegram conversation."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="telegram_account", verbose_name="користувач")
    chat_id = models.BigIntegerField("Telegram chat ID", blank=True, null=True, unique=True)
    link_code = models.CharField("код прив’язки", max_length=32, unique=True, default=generate_telegram_link_code, editable=False)
    linked_at = models.DateTimeField("прив’язано", blank=True, null=True)

    class Meta:
        verbose_name = "Telegram-акаунт"
        verbose_name_plural = "Telegram-акаунти"

    def __str__(self):
        return f"{self.user} — {'підключено' if self.chat_id else 'очікує підключення'}"


class ParentChild(models.Model):
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="child_links", verbose_name="батьки")
    child = models.ForeignKey(User, on_delete=models.CASCADE, related_name="parent_links", verbose_name="дитина")
    note = models.CharField("примітка", max_length=160, blank=True)
    created_at = models.DateTimeField("створено", auto_now_add=True)

    class Meta:
        verbose_name = "зв'язок батьки-дитина"
        verbose_name_plural = "зв'язки батьків і дітей"
        unique_together = ["parent", "child"]

    def __str__(self):
        return f"{self.parent} -> {self.child}"


class Course(models.Model):
    class Direction(models.TextChoices):
        ENGLISH = "english", "Англійська мова"
        ROBOTICS = "robotics", "Робототехніка"
        WEB = "web", "Веб-програмування"

    title = models.CharField("назва", max_length=160)
    direction = models.CharField("напрям", max_length=20, choices=Direction.choices)
    age_range = models.CharField("вік", max_length=80)
    level = models.CharField("рівень", max_length=80, blank=True)
    schedule = models.CharField("частота занять", max_length=120)
    price = models.CharField("вартість", max_length=120)
    final_project = models.CharField("підсумок", max_length=180)
    short_description = models.TextField("короткий опис")
    is_published = models.BooleanField("опубліковано", default=True)
    created_at = models.DateTimeField("створено", auto_now_add=True)

    class Meta:
        verbose_name = "курс"
        verbose_name_plural = "курси"
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("course_detail", kwargs={"pk": self.pk})


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules", verbose_name="курс")
    title = models.CharField("назва", max_length=160)
    description = models.TextField("опис", blank=True)
    order = models.PositiveIntegerField("порядок", default=1)

    class Meta:
        verbose_name = "модуль"
        verbose_name_plural = "модулі"
        ordering = ["course", "order"]

    def __str__(self):
        return f"{self.course}: {self.title}"


class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons", verbose_name="модуль")
    title = models.CharField("назва", max_length=180)
    summary = models.TextField("коротко про урок", blank=True)
    content = models.TextField("матеріал уроку", blank=True)
    video_url = models.URLField("відео або зустріч", blank=True)
    order = models.PositiveIntegerField("порядок", default=1)
    is_available = models.BooleanField("доступний", default=True)

    class Meta:
        verbose_name = "урок"
        verbose_name_plural = "уроки"
        ordering = ["module", "order"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("lesson_detail", kwargs={"pk": self.pk})


class LessonStep(models.Model):
    class Kind(models.TextChoices):
        TOPIC = "topic", "Тема уроку"
        MATERIALS = "materials", "Матеріали"
        VOCABULARY = "vocabulary", "Слова"
        HOMEWORK = "homework", "Домашнє завдання"
        QUIZ = "quiz", "Тест"

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="steps", verbose_name="урок")
    kind = models.CharField("тип кроку", max_length=20, choices=Kind.choices)
    order = models.PositiveIntegerField("порядок", default=1)

    class Meta:
        verbose_name = "крок уроку"
        verbose_name_plural = "кроки уроку"
        ordering = ["lesson", "order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["lesson", "kind"], name="unique_lesson_step_kind"),
        ]

    def __str__(self):
        return f"{self.lesson}: {self.get_kind_display()}"


class Material(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="materials", verbose_name="урок")
    title = models.CharField("назва", max_length=180)
    file = models.FileField("файл", upload_to="materials/", blank=True)
    external_url = models.URLField("посилання", blank=True)
    description = models.TextField("опис", blank=True)
    is_code = models.BooleanField("це код — показати кнопку «Скопіювати код»", default=False)

    class Meta:
        verbose_name = "матеріал"
        verbose_name_plural = "матеріали"

    def __str__(self):
        return self.title

    @property
    def should_render_as_code(self):
        return self.is_code or self.title.strip().lower() in {"код", "code", "program code"}


class VocabularySet(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="vocabulary_sets", verbose_name="урок")
    title = models.CharField("назва списку", max_length=180)
    description = models.TextField("пояснення", blank=True)
    order = models.PositiveIntegerField("порядок", default=1)
    is_published = models.BooleanField("опубліковано", default=True)

    class Meta:
        verbose_name = "список слів"
        verbose_name_plural = "списки слів"
        ordering = ["lesson", "order", "title"]

    def __str__(self):
        return self.title


class VocabularyWord(models.Model):
    vocabulary_set = models.ForeignKey(VocabularySet, on_delete=models.CASCADE, related_name="words", verbose_name="список")
    word = models.CharField("слово або фраза", max_length=140)
    translation = models.CharField("переклад / пояснення", max_length=220, blank=True)
    example = models.TextField("приклад", blank=True)
    order = models.PositiveIntegerField("порядок", default=1)

    class Meta:
        verbose_name = "слово"
        verbose_name_plural = "слова"
        ordering = ["vocabulary_set", "order", "word"]

    def __str__(self):
        return self.word


class StudentWord(models.Model):
    class Status(models.TextChoices):
        UNKNOWN = "unknown", "Не знаю"
        LEARNING = "learning", "Вчу"
        KNOWN = "known", "Знаю"

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="word_progress", verbose_name="учень")
    word = models.ForeignKey(VocabularyWord, on_delete=models.CASCADE, related_name="student_progress", verbose_name="слово")
    status = models.CharField("статус", max_length=20, choices=Status.choices, default=Status.UNKNOWN)
    created_at = models.DateTimeField("додано", auto_now_add=True)
    updated_at = models.DateTimeField("оновлено", auto_now=True)

    class Meta:
        verbose_name = "слово учня"
        verbose_name_plural = "слова учнів"
        unique_together = ["student", "word"]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.student} - {self.word}: {self.get_status_display()}"


class MaterialAttachment(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name="attachments", verbose_name="матеріал")
    title = models.CharField("назва", max_length=180)
    file = models.FileField("файл або скрін", upload_to="materials/attachments/", blank=True)
    external_url = models.URLField("відео або посилання", blank=True)
    note = models.CharField("пояснення", max_length=220, blank=True)
    order = models.PositiveIntegerField("порядок", default=1)

    class Meta:
        verbose_name = "вкладення матеріалу"
        verbose_name_plural = "вкладення матеріалів"
        ordering = ["material", "order", "title"]

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments", verbose_name="учень")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments", verbose_name="курс")
    started_at = models.DateField("дата старту")
    is_active = models.BooleanField("активне навчання", default=True)

    class Meta:
        verbose_name = "зарахування"
        verbose_name_plural = "зарахування"
        unique_together = ["student", "course"]

    def __str__(self):
        return f"{self.student} - {self.course}"


class Assignment(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="assignments", verbose_name="урок")
    title = models.CharField("назва", max_length=180)
    task = models.TextField("завдання")
    due_date = models.DateField("дедлайн", blank=True, null=True)
    max_points = models.PositiveIntegerField("максимум балів", default=100)

    class Meta:
        verbose_name = "домашнє завдання"
        verbose_name_plural = "домашні завдання"

    def __str__(self):
        return self.title


class ScheduleEntry(models.Model):
    """A personal class that repeats every week for one student."""

    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Понеділок"
        TUESDAY = 1, "Вівторок"
        WEDNESDAY = 2, "Середа"
        THURSDAY = 3, "Четвер"
        FRIDAY = 4, "П’ятниця"
        SATURDAY = 5, "Субота"
        SUNDAY = 6, "Неділя"

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="schedule_entries", verbose_name="учень")
    title = models.CharField("назва заняття", max_length=180)
    weekday = models.PositiveSmallIntegerField("день тижня", choices=Weekday.choices)
    starts_at = models.TimeField("час початку")
    ends_at = models.TimeField("час завершення", blank=True, null=True)
    teacher = models.CharField("викладач", max_length=140, blank=True)
    location = models.CharField("місце або аудиторія", max_length=180, blank=True)
    meeting_url = models.URLField("посилання на онлайн-зустріч", blank=True)
    note = models.TextField("примітка", blank=True)
    is_cancelled = models.BooleanField("скасовано", default=False)
    created_at = models.DateTimeField("створено", auto_now_add=True)

    class Meta:
        verbose_name = "заняття в розкладі"
        verbose_name_plural = "розклад занять"
        ordering = ["student__last_name", "student__first_name", "weekday", "starts_at"]

    def __str__(self):
        return f"{self.student}: {self.get_weekday_display()} {self.starts_at:%H:%M} — {self.title}"


class HomeworkNotification(models.Model):
    """Delivery record for the initial Telegram homework announcement."""

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="telegram_notifications")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="homework_notifications")
    sent_at = models.DateTimeField("надіслано", blank=True, null=True)
    error = models.TextField("помилка", blank=True)

    class Meta:
        verbose_name = "сповіщення про домашнє завдання"
        verbose_name_plural = "сповіщення про домашні завдання"
        constraints = [models.UniqueConstraint(fields=["assignment", "recipient"], name="unique_homework_notification")]


class ScheduleException(models.Model):
    """A one-date override of a student's recurring weekly class."""

    schedule_entry = models.ForeignKey(ScheduleEntry, on_delete=models.CASCADE, related_name="exceptions", verbose_name="заняття розкладу")
    date = models.DateField("дата")
    title = models.CharField("інша назва заняття", max_length=180, blank=True)
    starts_at = models.TimeField("інший час початку", blank=True, null=True)
    ends_at = models.TimeField("інший час завершення", blank=True, null=True)
    location = models.CharField("інше місце або аудиторія", max_length=180, blank=True)
    meeting_url = models.URLField("інше посилання на онлайн-зустріч", blank=True)
    note = models.TextField("примітка", blank=True)
    is_cancelled = models.BooleanField("скасувати заняття цього дня", default=False)

    class Meta:
        verbose_name = "зміна розкладу на дату"
        verbose_name_plural = "зміни розкладу на окремі дати"
        ordering = ["date"]
        constraints = [models.UniqueConstraint(fields=["schedule_entry", "date"], name="unique_schedule_exception_date")]

    def __str__(self):
        return f"{self.schedule_entry} — {self.date:%d.%m.%Y}"


class TelegramBroadcast(models.Model):
    """A teacher-created Telegram announcement for selected students."""

    title = models.CharField("назва розсилки", max_length=180)
    message = models.TextField("текст повідомлення")
    recipients = models.ManyToManyField(User, related_name="telegram_broadcasts", blank=True, verbose_name="одержувачі")
    created_at = models.DateTimeField("створено", auto_now_add=True)
    sent_at = models.DateTimeField("останнє надсилання", blank=True, null=True)

    class Meta:
        verbose_name = "розсилка Telegram"
        verbose_name_plural = "розсилки Telegram"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class LessonReminder(models.Model):
    """Makes the 24-hour schedule reminder safe to run repeatedly."""

    schedule_entry = models.ForeignKey(ScheduleEntry, on_delete=models.CASCADE, related_name="reminders")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lesson_reminders")
    occurrence_date = models.DateField("дата заняття")
    lead_hours = models.PositiveSmallIntegerField("годин до заняття")
    sent_at = models.DateTimeField("надіслано", blank=True, null=True)
    error = models.TextField("помилка", blank=True)

    class Meta:
        verbose_name = "нагадування про заняття"
        verbose_name_plural = "нагадування про заняття"
        constraints = [models.UniqueConstraint(fields=["schedule_entry", "recipient", "occurrence_date", "lead_hours"], name="unique_schedule_reminder")]


class Quiz(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="quizzes", verbose_name="урок")
    title = models.CharField("назва тесту", max_length=180)
    description = models.TextField("опис", blank=True)
    reading_title = models.CharField("заголовок тексту для reading", max_length=180, blank=True)
    reading_text = models.TextField("спільний текст для reading", blank=True)
    max_points = models.PositiveIntegerField("максимум балів", default=100)
    passing_percent = models.PositiveIntegerField("прохідний відсоток", default=60)
    is_graded = models.BooleanField("показувати оцінку", default=True)
    is_published = models.BooleanField("опубліковано", default=True)
    allow_retakes = models.BooleanField("дозволити повторне проходження", default=True)
    order = models.PositiveIntegerField("порядок", default=1)

    class Meta:
        verbose_name = "тест"
        verbose_name_plural = "тести"
        ordering = ["lesson", "order", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("take_quiz", kwargs={"pk": self.pk})


class QuizQuestion(models.Model):
    class Type(models.TextChoices):
        CHOICE = "choice", "Обрати правильну відповідь"
        TEXT = "text", "Вписати відповідь / заповнити пропуск"
        DRAG = "drag", "Перетягнути відповідь у пропуск"

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions", verbose_name="тест")
    question_type = models.CharField("тип питання", max_length=16, choices=Type.choices, default=Type.CHOICE)
    context_text = models.TextField("текст або уривок до питання", blank=True)
    audio_file = models.FileField("аудіо для listening", upload_to="quizzes/audio/", blank=True)
    audio_url = models.URLField("пряме посилання на аудіо", blank=True)
    image_file = models.ImageField("зображення до питання", upload_to="quizzes/images/", blank=True)
    image_url = models.URLField("посилання на зображення", blank=True)
    text = models.TextField("питання")
    correct_answer = models.CharField("правильна текстова відповідь", max_length=255, blank=True)
    drag_options = models.TextField("варіанти для перетягування", blank=True, help_text="Кожен варіант з нового рядка")
    explanation = models.TextField("пояснення після відповіді", blank=True)
    order = models.PositiveIntegerField("порядок", default=1)
    is_active = models.BooleanField("активне", default=True)

    class Meta:
        verbose_name = "питання тесту"
        verbose_name_plural = "питання тестів"
        ordering = ["quiz", "order", "id"]

    def __str__(self):
        return self.text[:80]

    @property
    def drag_option_list(self):
        return [option.strip() for option in self.drag_options.splitlines() if option.strip()]


class QuizChoice(models.Model):
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name="choices", verbose_name="питання")
    text = models.CharField("варіант відповіді", max_length=255)
    is_correct = models.BooleanField("правильна відповідь", default=False)
    order = models.PositiveIntegerField("порядок", default=1)

    class Meta:
        verbose_name = "варіант відповіді"
        verbose_name_plural = "варіанти відповідей"
        ordering = ["question", "order", "id"]

    def __str__(self):
        return self.text


class AttendanceSession(models.Model):
    """A teacher's attendance register for one course meeting."""

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="attendance_sessions", verbose_name="курс")
    date = models.DateField("дата заняття")
    title = models.CharField("тема або назва заняття", max_length=180, blank=True)
    created_at = models.DateTimeField("створено", auto_now_add=True)

    class Meta:
        verbose_name = "заняття в журналі відвідуваності"
        verbose_name_plural = "журнал відвідуваності"
        ordering = ["-date", "course__title"]
        constraints = [models.UniqueConstraint(fields=["course", "date"], name="unique_attendance_course_date")]

    def __str__(self):
        return f"{self.course} — {self.date:%d.%m.%Y}"


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = "present", "Був/була"
        ABSENT = "absent", "Відсутній/відсутня"
        LATE = "late", "Запізнився/запізнилась"
        EXCUSED = "excused", "Поважна причина"

    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="records", verbose_name="заняття")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attendance_records", verbose_name="учень")
    status = models.CharField("статус", max_length=20, choices=Status.choices, default=Status.PRESENT)
    note = models.CharField("примітка", max_length=180, blank=True)

    class Meta:
        verbose_name = "відмітка відвідуваності"
        verbose_name_plural = "відмітки відвідуваності"
        constraints = [models.UniqueConstraint(fields=["session", "student"], name="unique_attendance_session_student")]
        ordering = ["student__first_name", "student__last_name", "student__username"]

    def __str__(self):
        return f"{self.student} — {self.session}: {self.get_status_display()}"


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts", verbose_name="тест")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_attempts", verbose_name="учень")
    correct_count = models.PositiveIntegerField("правильних відповідей", default=0)
    total_count = models.PositiveIntegerField("усього питань", default=0)
    score_percent = models.PositiveIntegerField("відсоток", default=0)
    points = models.PositiveIntegerField("бали", default=0)
    started_at = models.DateTimeField("розпочато", auto_now_add=True)
    completed_at = models.DateTimeField("завершено", auto_now=True)

    class Meta:
        verbose_name = "результат тесту"
        verbose_name_plural = "результати тестів"
        ordering = ["-completed_at"]

    @property
    def is_passed(self):
        return self.score_percent >= self.quiz.passing_percent

    def __str__(self):
        return f"{self.student} - {self.quiz}: {self.score_percent}%"


class QuizAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="answers", verbose_name="спроба")
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name="answers", verbose_name="питання")
    selected_choice = models.ForeignKey(QuizChoice, on_delete=models.SET_NULL, related_name="answers", verbose_name="обрана відповідь", blank=True, null=True)
    text_answer = models.CharField("текстова відповідь учня", max_length=255, blank=True)
    is_correct = models.BooleanField("правильно", default=False)

    class Meta:
        verbose_name = "відповідь у тесті"
        verbose_name_plural = "відповіді у тестах"
        ordering = ["attempt", "question__order", "question_id"]

    def __str__(self):
        return f"{self.question} - {self.selected_choice}"


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions", verbose_name="завдання")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submissions", verbose_name="учень")
    answer = models.TextField("відповідь", blank=True)
    file = models.FileField("файл роботи", upload_to="submissions/", blank=True)
    submitted_at = models.DateTimeField("здано", auto_now_add=True)
    updated_at = models.DateTimeField("оновлено", auto_now=True)
    points = models.PositiveIntegerField("бали", blank=True, null=True)
    is_reviewed = models.BooleanField("перевірено", default=False)
    teacher_comment = models.TextField("коментар викладача", blank=True)

    class Meta:
        verbose_name = "здана робота"
        verbose_name_plural = "здані роботи"
        ordering = ["-submitted_at"]
        unique_together = ["assignment", "student"]

    def __str__(self):
        return f"{self.student} - {self.assignment}"


class SubmissionAttachment(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="attachments", verbose_name="здана робота")
    title = models.CharField("назва", max_length=180, blank=True)
    file = models.FileField("файл або скрін", upload_to="submissions/attachments/", blank=True)
    external_url = models.URLField("відео або посилання", blank=True)
    note = models.CharField("пояснення", max_length=220, blank=True)
    created_at = models.DateTimeField("додано", auto_now_add=True)

    class Meta:
        verbose_name = "вкладення роботи"
        verbose_name_plural = "вкладення робіт"
        ordering = ["created_at"]

    def __str__(self):
        return self.title or self.external_url or self.file.name


class LessonProgress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lesson_progress", verbose_name="учень")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress", verbose_name="урок")
    is_done = models.BooleanField("пройдено", default=False)
    updated_at = models.DateTimeField("оновлено", auto_now=True)

    class Meta:
        verbose_name = "прогрес уроку"
        verbose_name_plural = "прогрес уроків"
        unique_together = ["student", "lesson"]

    def __str__(self):
        return f"{self.student} - {self.lesson}"
