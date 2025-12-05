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
    user_portfolio = Portfolio(user_id, {"USD": 1000})
    portfolios.append(user_portfolio.to_dict())
    save_portfolios(portfolios)

    # Шаг 6: Выводим сообщение об успехе
    print(f"Пользователь '{username}' зарегистрирован (id={user_id}). Войдите: login --username {username} --password ****")
    
    
    
def login_user(username: str, password: str):
    """Выполняет вход пользователя в систему."""
    users = load_users()
    
    # Шаг 1: Найти пользователя по username
    user = None
    for u in users.values():
        if u.username == username:
            user = u
            break
    
    if not user:
        print(f"Пользователь '{username}' не найден")
        return
    
    # Шаг 2: Сравнить хеш пароля
    if user.verify_password(password):
        print(f"Вы вошли как '{username}'")
    else:
        print("Неверный пароль")
        
        
def show_portfolio(username: str, base: str = "USD"):
    """
    Показывает портфель пользователя в заданной базовой валюте.
    """
    users = load_users()
    portfolios = load_portfolios()

    # Шаг 1: Убедиться, что пользователь залогинен (есть в users)
    user = None
    for u in users.values():
        if u.username == username:
            user = u
            break

    if not user:
        print("Сначала выполните login")
        return

    user_id = user.user_id
    print(user_id)
    # Шаг 2: Загрузить портфель пользователя
    portfolio = []
    for p in portfolios:
        if user_id in list(p.values()):
            portfolio = p["wallets"]
            break


    if not portfolio:
        print(f"Портфель пользователя '{username}' пуст")
        return

    # Курсы валют (в реальности нужно брать из API; здесь — заглушка)
    exchange_rates = {
        "USD": 1.0,
        "EUR": 1.07,
        "BTC": 59300.0,  # примерная стоимость
        "GBP": 1.26,
        "JPY": 0.0067,
    }

    # Проверить, что базовая валюта известна
    if base not in exchange_rates:
        print(f"Неизвестная базовая валюта '{base}'")
        return

    base_rate = exchange_rates[base]

    print(f"\nПортфель пользователя '{username}' (база: {base}):")
    total_in_base = 0.0

    # Шаг 4: Для каждого кошелька
    for currency, balance in portfolio.items():
        if currency not in exchange_rates:
            print(f"  - {currency}: {balance:.2f} → курс неизвестен")
            continue

        # Стоимость в базовой валюте
        rate = exchange_rates[currency]
        value_in_base = balance * (rate / base_rate)
        total_in_base += value_in_base


        print(f"  - {currency}: {balance:.2f} → {value_in_base:.2f} {base}")


    # Шаг 5: Итоговая сумма
    print("-" * 40)
    print(f"ИТОГО: {total_in_base:.2f} {base}\n")
