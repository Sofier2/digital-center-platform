# Внутрішня навчальна платформа

Django-проєкт для Центру цифрових технологій: кабінет учня, батьківський кабінет, курси, уроки, матеріали, домашні завдання, здача робіт, оцінювання та внутрішня панель викладача.

## Локальний запуск

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

Основні адреси:

- Кабінет: `http://127.0.0.1:8000/`
- Вхід: `http://127.0.0.1:8000/accounts/login/`
- Django admin: `http://127.0.0.1:8000/admin/`
- Панель викладача: `http://127.0.0.1:8000/manage/`

## Файли, скріни й відео

У production завантажені матеріали та домашні роботи мають зберігатися в Cloudinary. Render не підходить як постійне файлове сховище: локальна папка `media/` може очиститися після redeploy або перезапуску.

Обов'язково додай на Render:

```env
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
```

Після цього нові завантаження будуть зберігатися в Cloudinary й відкриватися з платформи. Старі файли, які були завантажені до підключення Cloudinary у локальне сховище Render, можуть не відновитися, якщо Render уже видалив їх із контейнера.

## Render environment variables

```env
SECRET_KEY=generated-by-render
DEBUG=False
ALLOWED_HOSTS=digital-center-platform.onrender.com
CSRF_TRUSTED_ORIGINS=https://digital-center-platform.onrender.com
DATABASE_URL=from Render PostgreSQL
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=your-password
PYTHON_VERSION=3.12.4
```

## Render commands

Build command:

```bash
bash build.sh
```

Start command:

```bash
gunicorn config.wsgi:application
```
