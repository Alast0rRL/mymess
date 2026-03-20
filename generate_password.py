#!/usr/bin/env python3
"""
Скрипт для генерации хэша пароля администратора.
Использование: python generate_password.py ваш_пароль
"""

import sys
from werkzeug.security import generate_password_hash

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python generate_password.py <ваш_пароль>")
        print("\nПример:")
        print("  python generate_password.py MySecurePassword123")
        sys.exit(1)
    
    password = sys.argv[1]
    password_hash = generate_password_hash(password)
    
    print("\n" + "=" * 60)
    print("Хэш пароля для .env файла:")
    print("=" * 60)
    print(f"ADMIN_PASSWORD_HASH={password_hash}")
    print("=" * 60)
    print("\nДобавьте эту строку в ваш .env файл")
