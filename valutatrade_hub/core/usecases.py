import datetime
import hashlib
import json
import os
from typing import Dict

from valutatrade_hub.core.models import User, Portfolio, ExchangeRates


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

def save_portfolios(portfolios):
    """Сохраняет портфели в portfolios.json."""
    # Преобразуем список Portfolio в список словарей
    data = [portfolio.to_dict() for portfolio in portfolios]
    
    with open(PORTFOLIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_salt() -> str:
    """Генерирует случайную соль."""
    return hashlib.sha256(os.urandom(32)).hexdigest()[:16]

def register_user(username: str, password: str):
    """Регистрирует нового пользователя."""
    # Шаг 1: Загружаем существующих пользователей
    users = User.load_users()


    # Проверяем уникальность username
    if any(user.username == username for user in users.values()):
        raise ValueError(f"Имя пользователя '{username}' уже занято")
        

    # Проверяем длину пароля
    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")


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
    users = User.load_users()
    portfolios = Portfolio.load_from_file(PORTFOLIOS_FILE)
    
    # Шаг 1: Найти пользователя по username
    user = None
    for u in users.values():
        if u.username == username:
            user = u
            break
    
    if not user:
        raise ValueError(f"Пользователь '{username}' не найден")
        
        
    for i, p in enumerate(portfolios):
        if p.user == user.user_id:
            portfolio = p    
    
    
    # Шаг 2: Сравнить хеш пароля
    if user.verify_password(password):
        print(f"Вы вошли как '{username}'")
    else:
        raise ValueError("Неверный пароль")
    return user, portfolio
        
        
def show_portfolio(user: User, portfolio: Portfolio, er: Dict, base_currency: str):
    """
    Показывает портфель пользователя в заданной базовой валюте.
    """
    
   # portfolios = Portfolio.load_from_file(PORTFOLIOS_FILE)   



    if not user:
        print("Сначала выполните login")
        return

   # user_id = user.user_id
   # print(user_id)
    # Шаг 2: Загрузить портфель пользователя
   # portfolio = {}

            
   # for i, p in enumerate(portfolios):
   #     if p.user == user.user_id:
    #        portfolio = p


    if not portfolio:
        print(f"Портфель пользователя '{user.username}' пуст")
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
    if base_currency not in er.exchange_rate_default:
        print(f"Неизвестная базовая валюта '{base_currency}'")
        return

   

    print(f"\nПортфель пользователя '{user.username}' (база: {base_currency}):")
    
    print(portfolio.wallets)
    for code, wallet in  portfolio.wallets.items():
        rate = er.exchange_rate_default[code] / er.exchange_rate_default[base_currency]
        print(f"- {code}: {wallet.balance} -> {rate*wallet.balance} {base_currency}")

    total_in_base = portfolio.get_total_value(base_currency)

    print(portfolio.to_dict())

    # Шаг 5: Итоговая сумма
    print("-" * 40)
    print(f"ИТОГО: {total_in_base:.2f} {base_currency}\n")
    
    
def buy(user: User, currency: str, amount: float, base_currency: str = "USD"):
    
    """
     Команда покупки валюты.
    
    :param portfolio: объект Portfolio пользователя
    :param currency: код валюты (например, 'BTC')
    :param amount: количество валюты для покупки (должно быть > 0)
    :param base_currency: базовая валюта для расчёта стоимости (по умолчанию USD)
    :return: строка с результатом выполнения команды
    """
    if not user:
        return "Пожалуйста, авторизуйтесь."

    index = None
    portfolios = Portfolio.load_from_file(PORTFOLIOS_FILE)
    for i, p in enumerate(portfolios):
        if p.user == user.user_id:
            index = i
            portfolio = p
               



    if portfolio is None:
        raise "Портфель пуст"

    # Шаг 2. Валидировать аргументы
    if not isinstance(currency, str) or not currency.strip():
        raise ValueError("Ошибка: код валюты не может быть пустым.")
    
    currency = currency.strip().upper()
    amount = float(amount)
    
    if not isinstance(amount, (int, float)):
        raise ValueError("'amount' должен быть числом.")
    
    
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом.")



    
    # Шаг 3. Проверить наличие кошелька, при отсутствии — создать
    try:
        if portfolio.get_wallet(currency) is None:
            portfolio.add_currency(currency)
    except ValueError as e:
        return f"Ошибка: {str(e)}"
        
    wallet_base_currency = portfolio.get_wallet(base_currency)
 
    current_balance =  wallet_base_currency.balance
    print(current_balance)
    # Шаг 4. Увеличить баланс кошелька

    # Шаг 5. Расчёт стоимости покупки (опционально)

    # Получаем курс валюты к базовой
    if currency not in portfolio.EXCHANGE_RATES:
        raise KeyError(f"Курс для {currency} не найден.")
        
    if base_currency not in portfolio.EXCHANGE_RATES:
        raise KeyError(f"Базовая валюта {base_currency} не поддерживается.")
        
    rate = portfolio.EXCHANGE_RATES[currency] / portfolio.EXCHANGE_RATES[base_currency]
    cost = amount * rate
    print(cost)
    print(current_balance)
    if current_balance < cost:
        raise ValueError("Недостаточно средств")
         
    wallet_currency = portfolio.get_wallet(currency)

            
    wallet_currency = portfolio.get_wallet(currency)    
  
    
    print(currency, amount)
        
         
    try:
        wallet_currency.deposit(amount)
        wallet_base_currency.withdraw(cost)
        print(wallet_currency.balance)
    except ValueError as e:
        return f"Ошибка при обновлении баланса: {str(e)}"
    
    portfolios[index] = portfolio
    save_portfolios(portfolios)
    
    
    print(portfolio.to_dict())
    return

    
def sell(user: User, currency: str, amount: float, base_currency: str = "USD"):
    
    """
     Команда продажи валюты.
    
    :param portfolio: объект Portfolio пользователя
    :param currency: код валюты (например, 'BTC')
    :param amount: количество валюты для покупки (должно быть > 0)
    :param base_currency: базовая валюта для расчёта стоимости (по умолчанию USD)
    :return: строка с результатом выполнения команды
    """
    if not user:
        return "Пожалуйста, авторизуйтесь."

    index = None
    portfolios = Portfolio.load_from_file(PORTFOLIOS_FILE)
    for i, p in enumerate(portfolios):
        if p.user == user.user_id:
            index = i
            portfolio = p
               



    if portfolio is None:
        raise "Портфель пуст"

    # Шаг 2. Валидировать аргументы
    if not isinstance(currency, str) or not currency.strip():
        raise ValueError("Ошибка: код валюты не может быть пустым.")
    
    currency = currency.strip().upper()
    amount = float(amount)
    
    if not isinstance(amount, (int, float)):
        raise ValueError("'amount' должен быть числом.")
    
    
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом.")



    

    try:
        if portfolio.get_wallet(currency) is None:
            raise ValueError("Валюты {currency} в кошельке нет")
    except ValueError as e:
        return f"Ошибка: {str(e)}"
        
    wallet_base_currency = portfolio.get_wallet(base_currency)
 
    current_balance =  wallet_base_currency.balance
    print(current_balance)
    # Шаг 4. Увеличить баланс кошелька

    # Шаг 5. Расчёт стоимости продажи (опционально)

    # Получаем курс валюты к базовой
    if currency not in portfolio.EXCHANGE_RATES:
        raise KeyError(f"Курс для {currency} не найден.")
        
    if base_currency not in portfolio.EXCHANGE_RATES:
        raise KeyError(f"Базовая валюта {base_currency} не поддерживается.")
        
    rate = portfolio.EXCHANGE_RATES[currency] / portfolio.EXCHANGE_RATES[base_currency]
    cost = amount * rate
    print(cost)
    print(current_balance)
    
    wallet_currency = portfolio.get_wallet(currency)  
    if wallet_currency.balance < amount:
        raise ValueError("Недостаточно средств")

    
    print(currency, amount)
        
         
    try:
        wallet_base_currency.deposit(cost)
        wallet_currency.withdraw(amount)
        print(wallet_currency.balance)
    except ValueError as e:
        return f"Ошибка при обновлении баланса: {str(e)}"
    
    portfolios[index] = portfolio
    save_portfolios(portfolios)
    
    
    print(portfolio.to_dict())
    return
