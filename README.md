# Внутрішня навчальна платформа

Django-проєкт для Центру цифрових технологій: особистий кабінет учня, курси, уроки, матеріали, домашні завдання, здачі робіт, прогрес і керування через Django admin.

## Що вже є

- Django admin для курсів, модулів, уроків, матеріалів, домашніх завдань, робіт учнів і прогресу.
- Кабінет учня із доступними курсами.
- Учень бачить тільки ті курси, які йому призначив викладач.
- Сторінка курсу з модулями та уроками.
- Сторінка уроку з матеріалами й домашніми завданнями.
- Здача домашніх завдань через текст, кілька файлів, скріни, відео та посилання.
- Матеріали уроків можуть мати кілька вкладень: файли, скріни, відео або зовнішні лінки.
- Внутрішня панель викладача: курси, студенти, доступи, перевірка робіт.
- Кабінет батьків із прогресом дітей, курсами, домашками, оцінками й коментарями.
- Оцінювання робіт із балами й коментарем.
- Стартова команда для трьох напрямків: англійська, робототехніка, веб-програмування.
- Адаптивний HTML/CSS інтерфейс окремо від лендингу.
- Favicon і знак платформи з логотипом центру.

## Запуск локально

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_courses
python manage.py runserver
```

Після запуску:

- Кабінет: `http://127.0.0.1:8000/`
- Вхід: `http://127.0.0.1:8000/accounts/login/`
- Адмінка: `http://127.0.0.1:8000/admin/`
- Панель викладача: `http://127.0.0.1:8000/manage/`

## Як наповнювати платформу

1. Зайти в Django admin.
2. Створити користувачів для учнів, батьків або викладачів.
3. Додати профіль користувача.
4. Додати або відредагувати курси.
5. У курсах створити модулі.
6. У модулях створити уроки.
7. До уроків додати матеріали й домашні завдання.
8. Через сторінку `Платформа -> Студенти` призначити дитині потрібні курси.
9. Перевіряти роботи у `Платформа -> Домашні роботи`.

## Кабінет батьків

1. Створити користувача для одного з батьків.
2. У профілі поставити роль `Батьки`.
3. У Django admin створити `ParentChild` або відкрити користувача-батька й додати дитину в inline-блоці.
4. Після входу батьки потрапляють у кабінет `/parents/` і бачать тільки прив'язаних дітей.

## Основна структура

```text
digital-center-platform/
  config/             # налаштування Django
  learning/           # моделі, admin, views, urls
  templates/learning/ # HTML сторінки платформи
  static/css/         # стилі інтерфейсу
  manage.py
  requirements.txt
```

## Наступні кроки

- Додати календар занять.
- Додати повідомлення про нові домашні завдання.
- Додати email-сповіщення для батьків і викладача.
- Налаштувати регулярні backup бази й файлів.

## Production: Render + PostgreSQL + Cloudinary

Проєкт підготовлений до деплою на Render:

- Django app запускається через `gunicorn`.
- Статичні файли збираються через `collectstatic` і віддаються WhiteNoise.
- База в production береться з `DATABASE_URL`, тобто Render PostgreSQL.
- Завантажені файли, скріни й відео в production йдуть у Cloudinary через `CLOUDINARY_URL`.
- Локально, якщо `DATABASE_URL` і `CLOUDINARY_URL` порожні, використовується SQLite і папка `media/`.

### Render environment variables

```env
SECRET_KEY=generated-by-render
DEBUG=False
ALLOWED_HOSTS=your-platform.onrender.com
CSRF_TRUSTED_ORIGINS=https://your-platform.onrender.com
DATABASE_URL=from Render PostgreSQL
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
```

### Render commands

Build command:

```bash
bash build.sh
```

Start command:

```bash
gunicorn config.wsgi:application
```

Після першого деплою створи адміністратора в Render Shell:

```bash
python manage.py createsuperuser
```

Якщо треба стартові курси:

```bash
python manage.py seed_courses
```
