import os
from dotenv import load_dotenv

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
    
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin'
