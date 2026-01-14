import hashlib
import json
import os
from typing import Dict
from constants import USERS_FILE, PORTFOLIOS_FILE
from valutatrade_hub.core.models import User

def load_users():
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

def load_portfolios() -> list:
    """Загружает портфели из portfolios.json (ожидает список)."""
    if not os.path.exists(PORTFOLIOS_FILE):
        return []  # Возвращаем пустой список, если файла нет

    with open(PORTFOLIOS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Проверяем, что загруженные данные — это список
    if not isinstance(data, list):
        raise ValueError(f"Ожидался список в {PORTFOLIOS_FILE}, но получен {type(data)}")

    return data

def save_portfolios(portfolios):
    """Сохраняет портфели в portfolios.json."""    
    with open(PORTFOLIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(portfolios, f, ensure_ascii=False, indent=2)

def generate_salt() -> str:
    """Генерирует случайную соль."""
    return hashlib.sha256(os.urandom(32)).hexdigest()[:16]
