# InnoAuthor

Django-платформа для публикации проектов, формирования команд и взаимодействия авторов, экспертов и участников.

## Возможности

- регистрация, авторизация и профили пользователей;
- создание и ведение проектов: статусы, теги, приватность, изображения;
- приглашения в команду, заявки на участие и задачи по проекту;
- комментарии, жалобы и новости;
- раздел экспертов и заявки на платформе;
- отправка писем и восстановление пароля.

## Стек

- Python 3.10, Django 4+
- PostgreSQL 15
- Redis и Celery
- Docker Compose, Nginx, Gunicorn
- WhiteNoise, Pillow, ReportLab, qrcode

## Быстрый запуск через Docker

1. Создайте файл `.env` в корне проекта:

   ```env
   SECRET_KEY=your-secret-key
   POSTGRES_DB=innauthor_db
   POSTGRES_USER=innauthor_user
   POSTGRES_PASSWORD=innauthor_password
   POSTGRES_HOST=innauthor_db
   POSTGRES_PORT=5432
   EMAIL_HOST_USER=your@email.com
   EMAIL_HOST_PASSWORD=your-email-password
   ```

2. Создайте внешний volume для PostgreSQL (он указан в `docker-compose.yml`):

   ```bash
   docker volume create innoauthor_postgres_data
   ```

3. Запустите проект:

   ```bash
   docker compose up --build
   ```

4. Откройте http://localhost:8080

## Локальный запуск

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

Для локального запуска укажите в `.env` доступную базу PostgreSQL, например `POSTGRES_HOST=localhost`, затем выполните:

```bash
python manage.py migrate
python manage.py runserver
```

## Структура проекта

- `InnAuthor/` — настройки, маршрутизация и WSGI;
- `projects/` — проекты, команды, задачи, заявки и приглашения;
- `users/`, `accounts/` — пользователи и авторизация;
- `comments/` — комментарии;
- `indexglav/`, `startpage/`, `about/`, `exite/` — основные страницы, новости и разделы платформы;
- `templates/`, `static/`, `staticfiles/` — шаблоны и статические файлы;
- `Dockerfile`, `docker-compose.yml`, `nginx.conf` — запуск и деплой.

## Примечание

Файлы `.env`, `media/`, дампы базы данных и архивы документов не входят в репозиторий.
