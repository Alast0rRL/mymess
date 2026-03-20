import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import db, Post
from auth import check_password, login_required, is_admin


def get_file_type(filename: str) -> str:
    """Определение типа файла по расширению."""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    image_exts = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'}
    video_exts = {'mp4', 'webm', 'ogg', 'avi', 'mov', 'mkv'}
    
    if ext in image_exts:
        return 'image'
    elif ext in video_exts:
        return 'video'
    else:
        return 'file'


def validate_file_mime_type(file_stream) -> tuple[bool, str]:
    """
    Проверка MIME-типа файла по магическим байтам.
    Возвращает (успех, сообщение об ошибке).
    """
    try:
        import magic
        
        # Сохраняем позицию и читаем начало файла
        current_pos = file_stream.tell()
        file_stream.seek(0)
        file_header = file_stream.read(2048)
        file_stream.seek(current_pos)
        
        # Определяем MIME-тип
        mime = magic.Magic(mime=True)
        detected_mime = mime.from_buffer(file_header)
        
        # Разрешённые MIME-типы
        allowed_mimes = {
            # Изображения
            'image/png', 'image/jpeg', 'image/gif', 'image/webp', 
            'image/bmp', 'image/svg+xml',
            # Видео
            'video/mp4', 'video/webm', 'video/ogg', 'video/x-msvideo',
            'video/quicktime', 'video/x-matroska',
            # Документы
            'application/pdf',
            # Архивы
            'application/zip', 'application/x-rar-compressed', 
            'application/x-7z-compressed', 'application/x-tar',
            'application/gzip', 'application/x-gzip'
        }
        
        if detected_mime not in allowed_mimes:
            return False, f'Недопустимый тип файла: {detected_mime}'
        
        return True, ''
    except ImportError:
        # Если python-magic не установлен, пропускаем проверку
        return True, ''
    except Exception as e:
        # В случае ошибки логируем, но пропускаем файл
        print(f"Warning: MIME check failed: {e}")
        return True, ''


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Инициализация CSRF защиты
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    # Whitelist для HTMX запросов
    @app.before_request
    def handle_csrf_for_htmx():
        """Обработка CSRF для HTMX запросов."""
        if request.headers.get('HX-Request'):
            # HTMX уже отправляет токен в заголовке X-CSRFToken
            pass
    
    db.init_app(app)
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    with app.app_context():
        db.create_all()
    
    @app.route('/')
    def index():
        posts = Post.query.order_by(Post.created_at.desc()).all()
        return render_template('index.html', posts=posts)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            password = request.form.get('password')
            if check_password(password):
                session['logged_in'] = True
                return redirect(url_for('index'))
            flash('Неверный пароль', 'error')
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        session.pop('logged_in', None)
        return redirect(url_for('index'))
    
    @app.route('/create', methods=['POST'])
    @login_required
    def create_post():
        content = request.form.get('content', '').strip()
        file = request.files.get('file')
        
        # Определяем тип поста
        post_type = 'text'
        file_path = None
        
        # Если есть файл - определяем его тип
        if file and file.filename:
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            if ext not in app.config['ALLOWED_EXTENSIONS']:
                flash(f'Недопустимый тип файла. Разрешены: изображения, видео, PDF, архивы', 'error')
                return redirect(url_for('index'))
            
            # Проверка MIME-типа
            is_valid, error_msg = validate_file_mime_type(file.stream)
            if not is_valid:
                flash(error_msg, 'error')
                return redirect(url_for('index'))
            
            unique_filename = generate_unique_filename(filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            file_path = unique_filename
            post_type = get_file_type(filename)
        
        # Если нет файла, проверяем содержимое на ссылку
        elif content:
            url_pattern = re.compile(r'https?://\S+')
            if url_pattern.search(content):
                post_type = 'link'
        
        # Если ничего нет - ошибка
        if not content and not file_path:
            flash('Добавьте текст или файл', 'error')
            return redirect(url_for('index'))
        
        post = Post(type=post_type, content=content, file_path=file_path)
        db.session.add(post)
        db.session.commit()
        
        flash('Пост создан', 'success')
        return redirect(url_for('index'))
    
    @app.route('/delete/<int:post_id>', methods=['POST'])
    @login_required
    def delete_post(post_id):
        post = Post.query.get_or_404(post_id)
        
        if post.file_path:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], post.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        db.session.delete(post)
        db.session.commit()

        if request.headers.get('HX-Request'):
            # Возвращаем пустой ответ для HTMX
            return ''

        flash('Пост удален', 'success')
        return redirect(url_for('index'))
    
    @app.context_processor
    def inject_is_admin():
        return {'is_admin': is_admin()}
    
    # Security headers для всех ответов
    @app.after_request
    def add_security_headers(response):
        """Добавление заголовков безопасности."""
        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.tailwindcss.com unpkg.com; "
            "style-src 'self' 'unsafe-inline' fonts.googleapis.com; "
            "font-src fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "media-src 'self' blob:; "
            "frame-ancestors 'none';"
        )
        # Защита от MIME sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # Защита от clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        # XSS Protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # Permissions Policy
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response
    
    return app


def generate_unique_filename(filename: str) -> str:
    """Генерация уникального имени файла."""
    import uuid
    from datetime import datetime
    
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = uuid.uuid4().hex[:8]
    
    if ext:
        return f'{timestamp}_{unique_id}.{ext}'
    return f'{timestamp}_{unique_id}'


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8010)
