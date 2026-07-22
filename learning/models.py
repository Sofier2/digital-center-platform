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


class Quiz(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="quizzes", verbose_name="урок")
    title = models.CharField("назва тесту", max_length=180)
    description = models.TextField("опис", blank=True)
    reading_title = models.CharField("заголовок тексту для reading", max_length=180, blank=True)
    reading_text = models.TextField("спільний текст для reading", blank=True)
    max_points = models.PositiveIntegerField("максимум балів", default=100)
    passing_percent = models.PositiveIntegerField("прохідний відсоток", default=60)
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
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions", verbose_name="тест")
    context_text = models.TextField("текст або уривок до питання", blank=True)
    audio_file = models.FileField("аудіо для listening", upload_to="quizzes/audio/", blank=True)
    audio_url = models.URLField("пряме посилання на аудіо", blank=True)
    text = models.TextField("питання")
    explanation = models.TextField("пояснення після відповіді", blank=True)
    order = models.PositiveIntegerField("порядок", default=1)
    is_active = models.BooleanField("активне", default=True)

    class Meta:
        verbose_name = "питання тесту"
        verbose_name_plural = "питання тестів"
        ordering = ["quiz", "order", "id"]

    def __str__(self):
        return self.text[:80]


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
