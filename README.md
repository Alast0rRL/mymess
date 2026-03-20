# Freedom Stream

Минималистичный публичный веб-фид (стена) на Flask для публикации ссылок и файлов.

## Возможности

- 📝 Публикация текстовых постов
- 🔗 Публикация ссылок с авто-превращением в кликабельные URL
- 📁 Загрузка файлов (изображения, видео, PDF, архивы)
- 🔐 Авторизация администратора по паролю (хешированному)
- 🗑️ Удаление постов через HTMX без перезагрузки
- ✏️ Редактирование постов
- 🔍 Поиск и фильтрация по типу
- 📄 Пагинация (20 постов на странице)
- 🎨 Современный чистый дизайн

## Быстрый старт

### 1. Локальная разработка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Копирование .env
cp .env.example .env

# Генерация хэша пароля
python generate_password.py ваш_пароль

# Запуск
python app.py
```

Откройте http://127.0.0.1:8010/

### 2. Docker (Production)

```bash
# Копирование .env
cp .env.production .env

# Генерация секретов
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> .env
python generate_password.py ваш_пароль >> .env

# Запуск
docker-compose up -d
```

Откройте http://localhost:8010/

## Структура проекта

```
/project-root
│   app.py              # Основное приложение
│   models.py           # Модель Post
│   auth.py             # Авторизация
│   config.py           # Конфигурация
│   wsgi.py             # Точка входа для Gunicorn
│   generate_password.py # Скрипт генерации хэша пароля
│   Dockerfile          # Docker образ
│   docker-compose.yml  # Docker Compose
│   nginx.conf          # Конфигурация Nginx
├── .github/workflows/
│   └── ci-cd.yml       # GitHub Actions
├── static/
│   ├── uploads/        # Загруженные файлы
│   └── css/
│       └── style.css   # Кастомные стили
├── templates/
│   ├── base.html       # Базовый шаблон
│   ├── index.html      # Лента с поиском и фильтрами
│   ├── login.html      # Вход
│   └── edit.html       # Редактирование поста
└── logs/               # Логи приложения
```

## Развертывание

### Docker Compose (рекомендуется)

```bash
# Сборка и запуск
docker-compose up -d --build

# Просмотр логов
docker-compose logs -f web

# Остановка
docker-compose down
```

### Ручное развертывание

```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка .env
export FLASK_DEBUG=False
export SECRET_KEY=your-secret-key
export DATABASE_URL=postgresql://user:pass@localhost/dbname

# Миграции БД
flask db init  # только первый раз
flask db migrate -m "Initial migration"
flask db upgrade

# Запуск через Gunicorn
gunicorn -w 4 -b 0.0.0.0:8010 wsgi:app
```

### Nginx конфигурация

Пример для `/etc/nginx/sites-available/freedom-stream`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/uploads/ {
        alias /path/to/project/static/uploads/;
        expires 30d;
    }
}
```

## Безопасность

- ✅ Хеширование паролей (PBKDF2-SHA256)
- ✅ CSRF защита всех форм
- ✅ Security headers (CSP, X-Frame-Options, etc.)
- ✅ Безопасные session cookie (HttpOnly, SameSite)
- ✅ MIME-валидация загружаемых файлов
- ✅ Rate limiting (рекомендуется добавить)
- ✅ Логирование всех действий

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `SECRET_KEY` | Ключ для сессий | `dev-secret-key...` |
| `ADMIN_PASSWORD_HASH` | Хэш пароля админа | `admin` (хеширован) |
| `DATABASE_URL` | URL базы данных | SQLite файл |
| `FLASK_DEBUG` | Debug режим | `False` |
| `PORT` | Порт приложения | `8010` |
| `LOG_LEVEL` | Уровень логов | `INFO` |

## Миграции базы данных

```bash
# Инициализация (первый раз)
flask db init

# Создание новой миграции
flask db migrate -m "Description"

# Применение миграций
flask db upgrade

# Откат миграции
flask db downgrade -1
```

## Мониторинг

### Health check

```bash
curl http://localhost:8010/health
```

Ответ:
```json
{
  "status": "ok",
  "database": "connected",
  "timestamp": "2026-03-20T19:45:00.000000"
}
```

### Логи

- `logs/app.log` - логи приложения
- `docker-compose logs web` - логи в Docker

## CI/CD

GitHub Actions автоматически:
1. Запускает тесты при push/PR
2. Собирает Docker образ
3. Пушит в GitHub Container Registry
4. Деплоит при мерже в main

## Лицензия

MIT
