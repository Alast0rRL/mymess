import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from config import Config
from models import db, Post
from auth import check_password, login_required, is_admin


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    with app.app_context():
        db.create_all()
    
    @app.route('/')
    def index():
        posts = Post.query.order_by(Post.created_at.desc()).all()
        return render_template('index.html', posts=posts, is_admin=is_admin())
    
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
        post_type = request.form.get('type')
        content = request.form.get('content', '').strip()
        
        if not content:
            flash('Содержимое не может быть пустым', 'error')
            return redirect(url_for('index'))
        
        file_path = None
        
        if post_type == 'file':
            if 'file' not in request.files:
                flash('Файл не найден', 'error')
                return redirect(url_for('index'))
            
            file = request.files['file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                
                if ext not in app.config['ALLOWED_EXTENSIONS']:
                    flash(f'Недопустимый тип файла. Разрешены: {", ".join(app.config["ALLOWED_EXTENSIONS"])}', 'error')
                    return redirect(url_for('index'))
                
                unique_filename = generate_unique_filename(filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                file_path = unique_filename
                post_type = 'file'
            else:
                flash('Файл не выбран', 'error')
                return redirect(url_for('index'))
        
        elif post_type == 'link':
            url_pattern = re.compile(r'https?://\S+')
            if not url_pattern.search(content):
                post_type = 'text'
        
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
            return '', 204
        
        flash('Пост удален', 'success')
        return redirect(url_for('index'))
    
    @app.context_processor
    def utility_processor():
        return {'is_admin': is_admin}
    
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
