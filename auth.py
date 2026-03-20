from functools import wraps
from flask import session, redirect, url_for


def check_password(password: str) -> bool:
    """Проверка пароля администратора."""
    from config import Config
    return password == Config.ADMIN_PASSWORD


def login_required(f):
    """Декоратор для защиты маршрутов администратора."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def is_admin() -> bool:
    """Проверка, авторизован ли текущий пользователь как админ."""
    return session.get('logged_in', False)
