from django.core.management.base import BaseCommand

from learning.models import Course, Lesson, Module


class Command(BaseCommand):
    help = "Create starter courses, modules, and lessons for the learning platform."

    def handle(self, *args, **options):
        courses = [
            {
                "title": "Англійська мова",
                "direction": Course.Direction.ENGLISH,
                "age_range": "6-13 років",
                "level": "A0-A2",
                "schedule": "2 рази на тиждень",
                "price": "200 грн/год",
                "final_project": "Підсумкова робота через 6 місяців",
                "short_description": (
                    "Для дітей із самого нуля і до впевненого рівня A2: словниковий запас, "
                    "вимова, читання, письмо, аудіювання та розмовна практика."
                ),
                "modules": [
                    ("Start from zero", "Алфавіт, базові фрази, перші діалоги."),
                    ("Everyday English", "Слова й ситуації з життя дитини."),
                    ("A2 practice", "Говоріння, читання й підсумкова робота."),
                ],
            },
            {
                "title": "Робототехніка",
                "direction": Course.Direction.ROBOTICS,
                "age_range": "7-13 років",
                "level": "",
                "schedule": "1 раз на тиждень",
                "price": "375 грн / 1.5 год",
                "final_project": "Готовий робот через 6 місяців",
                "short_description": (
                    "Діти збирають механізми, працюють з логікою, датчиками й командними задачами. "
                    "У кінці навчання є готовий робот."
                ),
                "modules": [
                    ("Механіка", "Конструкції, рух, міцність і перші прототипи."),
                    ("Логіка робота", "Датчики, алгоритми й поведінка робота."),
                    ("Фінальний робот", "Збірка, тестування й презентація результату."),
                ],
            },
            {
                "title": "Веб-програмування",
                "direction": Course.Direction.WEB,
                "age_range": "13-16 років",
                "level": "",
                "schedule": "1 раз на тиждень",
                "price": "375 грн / 1.5 год",
                "final_project": "Готовий сайт через 6 місяців",
                "short_description": (
                    "Повний життєвий цикл веб-проєкту: ідея, дизайн, HTML/CSS, JavaScript, "
                    "GitHub, деплой і презентація готового сайту."
                ),
                "modules": [
                    ("HTML та структура", "Сторінки, семантика й акуратна розмітка."),
                    ("CSS та адаптив", "Колір, сітки, анімації й мобільна версія."),
                    ("GitHub і деплой", "Версії, публікація проєкту й фінальна презентація."),
                ],
            },
        ]

        for data in courses:
            module_titles = data.pop("modules")
            course, _ = Course.objects.update_or_create(
                title=data["title"],
                defaults=data,
            )
            for index, (title, description) in enumerate(module_titles, start=1):
                module, _ = Module.objects.update_or_create(
                    course=course,
                    title=title,
                    defaults={"description": description, "order": index},
                )
                Lesson.objects.update_or_create(
                    module=module,
                    title=f"Урок {index}. {title}",
                    defaults={
                        "summary": description,
                        "content": "Тут викладач додає матеріал уроку, посилання, вправи та пояснення.",
                        "order": index,
                        "is_available": True,
                    },
                )

        self.stdout.write(self.style.SUCCESS("Starter courses were created."))
