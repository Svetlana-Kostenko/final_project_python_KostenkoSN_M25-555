import json
import hashlib
import datetime
import argparse
import os
from typing import Dict, Any
from valutatrade_hub.core.models import *

# Пути к файлам данных
USERS_FILE = "data/users.json"
PORTFOLIOS_FILE = "data/portfolios.json"


def load_users() -> Dict[int, User]:
    """Загружает пользователей из users.json."""
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {user["user_id"]: User.from_dict(user) for user in data}

def save_users(users: Dict[int, User]):
    """Сохраняет пользователей в users.json."""
    data = [user.to_dict() for user in users.values()]
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_portfolios() -> Dict[int, Dict]:
    """Загружает портфели из portfolios.json."""
    if not os.path.exists(PORTFOLIOS_FILE):
        return {}
    with open(PORTFOLIOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_portfolios(portfolios: Dict[int, Dict]):
    """Сохраняет портфели в portfolios.json."""
    with open(PORTFOLIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(portfolios, f, ensure_ascii=False, indent=2)

def generate_salt() -> str:
    """Генерирует случайную соль."""
    return hashlib.sha256(os.urandom(32)).hexdigest()[:16]

def register_user(username: str, password: str):
    """Регистрирует нового пользователя."""
    # Шаг 1: Загружаем существующих пользователей
    users = load_users()

    # Проверяем уникальность username
    if any(user.username == username for user in users.values()):
        print(f"Имя пользователя '{username}' уже занято")
        return

    # Проверяем длину пароля
    if len(password) < 4:
        print("Пароль должен быть не короче 4 символов")
        return

    # Шаг 2: Генерируем user_id (автоинкремент)
    user_id = max(users.keys()) + 1 if users else 1

    # Шаг 3: Генерируем соль и хешируем пароль
    salt = generate_salt()
    password_salt = password + salt
    hashed_password = hashlib.sha256(password_salt.encode()).hexdigest()

    # Создаём объект User
    user = User(
        user_id=user_id,
        username=username,
        hashed_password=hashed_password,
        salt=salt,
        registration_date=datetime.datetime.now()
    )

    # Добавляем пользователя в словарь
    users[user_id] = user

    # Шаг 4: Сохраняем пользователей
    save_users(users)

    # Шаг 5: Создаём пустой портфель
    portfolios = load_portfolios()
    portfolios[user_id] = {}
    save_portfolios(portfolios)

    # Шаг 6: Выводим сообщение об успехе
    print(f"Пользователь '{username}' зарегистрирован (id={user_id}). Войдите: login --username {username} --password ****")

