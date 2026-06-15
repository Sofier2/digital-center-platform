from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


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
    notes = models.TextField("нотатки", blank=True)

    class Meta:
        verbose_name = "профіль"
        verbose_name_plural = "профілі"

    def __str__(self):
        return self.user.get_full_name() or self.user.username


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


class Material(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="materials", verbose_name="урок")
    title = models.CharField("назва", max_length=180)
    file = models.FileField("файл", upload_to="materials/", blank=True)
    external_url = models.URLField("посилання", blank=True)
    description = models.TextField("опис", blank=True)

    class Meta:
        verbose_name = "матеріал"
        verbose_name_plural = "матеріали"

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


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions", verbose_name="завдання")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submissions", verbose_name="учень")
    answer = models.TextField("відповідь", blank=True)
    file = models.FileField("файл роботи", upload_to="submissions/", blank=True)
    submitted_at = models.DateTimeField("здано", auto_now_add=True)
    points = models.PositiveIntegerField("бали", blank=True, null=True)
    teacher_comment = models.TextField("коментар викладача", blank=True)

    class Meta:
        verbose_name = "здана робота"
        verbose_name_plural = "здані роботи"
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.student} - {self.assignment}"


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
