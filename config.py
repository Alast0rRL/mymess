import os
from datetime import timedelta
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(BASE_DIR, "freedom_stream.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB max upload
    
    ALLOWED_EXTENSIONS = {
        # Изображения
        'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg',
        # Видео
        'mp4', 'webm', 'ogg', 'avi', 'mov', 'mkv',
        # Документы и архивы
        'pdf', 'zip', 'rar', '7z', 'tar', 'gz'
    }
    
    # Хэш пароля администратора (по умолчанию 'admin')
    # Для смены пароля используйте: generate_password_hash('ваш_пароль')
    ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH') or \
        generate_password_hash('admin')
    
    # Безопасные настройки сессий
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Включить True для HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    @staticmethod
    def verify_password(password: str) -> bool:
        """Проверка пароля против хэша."""
        return check_password_hash(Config.ADMIN_PASSWORD_HASH, password)
