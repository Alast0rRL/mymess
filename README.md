# Freedom Stream

Минималистичный публичный веб-фид (стена) на Flask для публикации ссылок и файлов.

## Возможности

- 📝 Публикация текстовых постов
- 🔗 Публикация ссылок с авто-превращением в кликабельные URL
- 📁 Загрузка файлов (изображения, PDF, архивы)
- 🔐 Авторизация администратора по паролю
- 🗑️ Удаление постов через HTMX без перезагрузки
- 🎨 Современный UI на Tailwind CSS

## Структура проекта

```
/project-root
│   app.py              # Основное приложение
│   models.py           # Модель Post
│   auth.py             # Авторизация
│   config.py           # Конфигурация
│   wsgi.py             # Точка входа для Gunicorn
├── static/uploads/     # Загруженные файлы
├── templates/
│   ├── base.html       # Базовый шаблон
│   ├── index.html      # Лента
│   └── login.html      # Вход
└── .env                # Переменные окружения
```

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте `.env` файл:
```bash
cp .env.example .env
```

3. Настройте переменные в `.env`:
```
SECRET_KEY=ваш-секретный-ключ
ADMIN_PASSWORD=ваш-пароль
DATABASE_URL=sqlite:///freedom_stream.db
```

4. Инициализируйте БД и запустите:
```bash
python app.py
```

## Развертывание с Gunicorn + Nginx

1. Запуск через Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

2. Пример конфига Nginx (`/etc/nginx/sites-available/freedom-stream`):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/project/static/;
        expires 30d;
    }
}
```

## Безопасность

- XSS защищено через экранирование в шаблонах Jinja2
- Загрузка файлов: `secure_filename()` + проверка расширений
- Макс. размер файла: 100 МБ
- Пароль администратора хранится в `.env`

## Лицензия

MIT
