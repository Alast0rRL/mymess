import os
import re
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
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


def setup_logging(app):
    """Настройка логирования приложения."""
    # Создаём папку для логов
    os.makedirs(app.config.get('LOG_FOLDER', 'logs'), exist_ok=True)
    
    # Rotating file handler
    file_handler = RotatingFileHandler(
        os.path.join(app.config.get('LOG_FOLDER', 'logs'), 'app.log'),
        maxBytes=app.config.get('LOG_MAX_BYTES', 10 * 1024 * 1024),
        backupCount=app.config.get('LOG_BACKUP_COUNT', 10)
    )
    file_handler.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO')))
    
    # Формат логов
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # Добавляем обработчик
    app.logger.addHandler(file_handler)
    app.logger.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO')))
    
    # Лог запуска
    app.logger.info('Freedom Stream startup')
    app.logger.info(f'Debug mode: {app.config.get("DEBUG", False)}')


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    # Настройка логирования
    setup_logging(app)
    
    # Инициализация CSRF защиты
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    # Инициализация миграций
    migrate = Migrate()
    migrate.init_app(app, db)
    
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
    
    # Маршруты будут добавлены ниже
    
    @app.route('/')
    def index():
        try:
            # Пагинация
            page = request.args.get('page', 1, type=int)
            per_page = 20
            
            # Поиск
            search = request.args.get('search', '').strip()
            
            # Фильтр по типу
            post_type = request.args.get('type', '').strip()
            
            # Сортировка
            sort = request.args.get('sort', 'newest')
            
            # Базовый запрос
            query = Post.query
            
            # Применяем поиск
            if search:
                query = query.filter(Post.content.ilike(f'%{search}%'))
            
            # Применяем фильтр по типу
            if post_type and post_type != 'all':
                query = query.filter(Post.type == post_type)
            
            # Применяем сортировку
            if sort == 'oldest':
                query = query.order_by(Post.created_at.asc())
            elif sort == 'type':
                query = query.order_by(Post.type.asc(), Post.created_at.desc())
            else:  # newest
                query = query.order_by(Post.created_at.desc())
            
            posts = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            return render_template(
                'index.html', 
                posts=posts.items, 
                pagination=posts,
                search=search,
                current_type=post_type,
                current_sort=sort
            )
        except Exception as e:
            app.logger.error(f'Error fetching posts: {e}')
            flash('Ошибка при загрузке ленты', 'error')
            return render_template('index.html', posts=[], pagination=None)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            password = request.form.get('password')
            try:
                if check_password(password):
                    session['logged_in'] = True
                    app.logger.info('Admin login successful')
                    return redirect(url_for('index'))
                else:
                    app.logger.warning(f'Failed login attempt from {request.remote_addr}')
                    flash('Неверный пароль', 'error')
            except Exception as e:
                app.logger.error(f'Login error: {e}')
                flash('Ошибка при входе', 'error')
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
        
        try:
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
                app.logger.info(f'File uploaded: {unique_filename} (type: {post_type})')
            
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
            
            app.logger.info(f'Post created: ID={post.id}, type={post_type}')
            flash('Пост создан', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error creating post: {e}')
            flash('Ошибка при создании поста', 'error')
            return redirect(url_for('index'))
    
    @app.route('/delete/<int:post_id>', methods=['POST'])
    @login_required
    def delete_post(post_id):
        try:
            post = Post.query.get_or_404(post_id)
            
            if post.file_path:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], post.file_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    app.logger.info(f'Deleted file: {post.file_path}')
            
            db.session.delete(post)
            db.session.commit()
            
            app.logger.info(f'Post deleted: ID={post_id}')
            
            if request.headers.get('HX-Request'):
                return ''
            
            flash('Пост удален', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error deleting post {post_id}: {e}')
            flash('Ошибка при удалении поста', 'error')
            return redirect(url_for('index'))
    
    @app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
    @login_required
    def edit_post(post_id):
        post = Post.query.get_or_404(post_id)
        
        if request.method == 'POST':
            try:
                content = request.form.get('content', '').strip()
                file = request.files.get('file')
                
                # Обновляем контент
                post.content = content
                
                # Если загружен новый файл
                if file and file.filename:
                    # Удаляем старый файл
                    if post.file_path:
                        old_path = os.path.join(app.config['UPLOAD_FOLDER'], post.file_path)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    
                    # Сохраняем новый
                    filename = secure_filename(file.filename)
                    unique_filename = generate_unique_filename(filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                    post.file_path = unique_filename
                    post.type = get_file_type(filename)
                    app.logger.info(f'File updated for post {post_id}: {unique_filename}')
                
                db.session.commit()
                app.logger.info(f'Post updated: ID={post_id}')
                flash('Пост обновлен', 'success')
                return redirect(url_for('index'))
                
            except Exception as e:
                db.session.rollback()
                app.logger.error(f'Error updating post {post_id}: {e}')
                flash('Ошибка при обновлении поста', 'error')
        
        return render_template('edit.html', post=post)
    
    @app.context_processor
    def inject_is_admin():
        return {'is_admin': is_admin()}
    
    # Health check endpoint
    @app.route('/health')
    def health():
        """Endpoint для мониторинга здоровья приложения."""
        from sqlalchemy import text
        
        try:
            # Проверяем подключение к БД
            db.session.execute(text('SELECT 1'))
            db_status = 'connected'
        except Exception as e:
            app.logger.error(f'Database health check failed: {e}')
            db_status = 'disconnected'
        
        status = 'ok' if db_status == 'connected' else 'degraded'
        return {
            'status': status,
            'database': db_status,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }, 200 if status == 'ok' else 503
    
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
    app.run(
        debug=app.config.get('DEBUG', False),
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8010))
    )
