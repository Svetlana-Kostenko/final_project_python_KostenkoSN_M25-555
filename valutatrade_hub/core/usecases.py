import datetime
import hashlib
import json
import os
from typing import Dict
from valutatrade_hub.core.exceptions import CurrencyNotFoundError, InsufficientFundsError
from valutatrade_hub.core.currencies import get_currency
from datetime import datetime
from typing import Tuple, Optional

from valutatrade_hub.core.models import User, Portfolio, Wallet, ExchangeRates, RateService


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

    
    with open(PORTFOLIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(portfolios, f, ensure_ascii=False, indent=2)

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
        registration_date=datetime.now()
    )

    # Добавляем пользователя в словарь
    users[user_id] = user

    # Шаг 4: Сохраняем пользователей
    save_users(users)

    # Шаг 5: Создаём пустой портфель
    portfolios = load_portfolios()
    currency = input("Введите валюту: ").strip().upper()
    amount = input("Введите баланс: ")
    
    try:
        if "." in amount:
            value = int(amount)
        else:
            value = float(amount)
    except:        
        raise TypeError("Баланс должен быть числом (int или float).")
    if value < 0:
            raise ValueError("Баланс не может быть отрицательным.")
    
    wallet_new_user = Wallet(currency, value)
    
    user_portfolio = Portfolio(user_id, {"USD":  wallet_new_user})
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



    if not portfolio:
        print(f"Портфель пользователя '{user.username}' пуст")
        return

    # Курсы валют (в реальности нужно брать из API; здесь — заглушка)
 #   exchange_rates = {
    #    "USD": 1.0,
    #    "EUR": 1.07,
    #    "BTC": 59300.0,  # примерная стоимость
   #     "GBP": 1.26,
   #     "JPY": 0.0067,
  #  }

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

    # Шаг 4. Увеличить баланс кошелька

    # Шаг 5. Расчёт стоимости покупки (опционально)

    # Получаем курс валюты к базовой
    if currency not in portfolio.EXCHANGE_RATES:
        raise KeyError(f"Курс для {currency} не найден.")
        
    if base_currency not in portfolio.EXCHANGE_RATES:
        raise KeyError(f"Базовая валюта {base_currency} не поддерживается.")
        
    rate = portfolio.EXCHANGE_RATES[currency] / portfolio.EXCHANGE_RATES[base_currency]
    cost = amount * rate

    if current_balance < cost:
        raise InsufficientFundsError(
                available=current_balance,
                required=cost,
                code=base_currency
            )        
         
    wallet_currency = portfolio.get_wallet(currency)

            
  
  
    

        
         
    try:
        wallet_currency.deposit(amount)
        wallet_base_currency.withdraw(cost)
        print(f"Покупка выполнена: {amount} {currency} по курсу {rate} {base_currency}/{currency}")
        print("Изменения в портфеле")
        print(f"- {currency}: было {wallet_currency.balance - amount} -> стало {wallet_currency.balance}")
        print(f"Оценочная стоимость покупки: {cost} {base_currency}")

    except ValueError as e:
        return f"Ошибка при обновлении баланса: {str(e)}"
    
    portfolios[index] = portfolio.to_dict()
    save_portfolios(portfolios)
    
    

    return portfolio

    
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

    # Шаг 4. Увеличить баланс кошелька

    # Шаг 5. Расчёт стоимости продажи (опционально)

    # Получаем курс валюты к базовой
    if currency not in portfolio.EXCHANGE_RATES:
        raise KeyError(f"Курс для {currency} не найден.")
        
    if base_currency not in portfolio.EXCHANGE_RATES:
        raise KeyError(f"Базовая валюта {base_currency} не поддерживается.")
        
    rate = portfolio.EXCHANGE_RATES[currency] / portfolio.EXCHANGE_RATES[base_currency]
    cost = amount * rate

    
    wallet_currency = portfolio.get_wallet(currency)  
    if wallet_currency.balance < amount:
        raise InsufficientFundsError(
            available=wallet_currency.balance,
            required=amount,
            code=currency
        )


        
         
    try:
        wallet_base_currency.deposit(cost)
        wallet_currency.withdraw(amount)
        print(f"Продажа выполнена: {amount} {currency} по курсу {rate} {base_currency}/{currency}")
        print("Изменения в портфеле")
        print(f"- {base_currency}: было {wallet_base_currency.balance - cost} -> стало {wallet_base_currency.balance}")
        print(f"Оценочная выружка: {cost} {base_currency}")

 
    except ValueError as e:
        return f"Ошибка при обновлении баланса: {str(e)}"
    
    portfolios[index] = portfolio.to_dict()
    save_portfolios(portfolios)

    return portfolio
    
    
def get_rate__old(from_curr, to_curr) -> str:
    """
    Обрабатывает команду get-rate.
    args — список аргументов после имени команды (например, ["--from", "USD", "--to", "BTC"]).
    """

    # 1. Валидация кодов валют
    if not from_curr or not to_curr:
        return "Ошибка: коды валют не могут быть пустыми."
    if not from_curr.isalpha() or not to_curr.isalpha():
        return "Ошибка: коды валют должны содержать только буквы."

    from_curr = from_curr.upper()
    to_curr = to_curr.upper()

        # 2. Получение курса
    rate_service = RateService()
    result = rate_service.get_rate(from_curr, to_curr)
    print(result)

    if result is None:
        print(f"Курс {from_curr}→{to_curr} недоступен. Повторите попытку позже.")

    rate, timestamp = result

        # 3. Формируем вывод
    dt = datetime.fromisoformat(timestamp)
    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")

    reverse_rate = 1 / rate if rate != 0 else 0

    print(
            f"Курс {from_curr}→{to_curr}: {rate:.8f} (обновлено: {formatted_time})\n"
            f"Обратный курс {to_curr}→{from_curr}: {reverse_rate:.2f}"
        )


def get_rate(from_curr: str, to_curr: str) -> str:
    """
    Обрабатывает команду get-rate: получает курс одной валюты к другой.
    
    Args:
        from_curr: код исходной валюты (например, 'USD')
        to_curr: код целевой валюты (например, 'BTC')
    
    Returns:
        Строка с результатом или сообщением об ошибке
    """
    try:
        # 1. Валидация входных параметров
        if not from_curr or not to_curr:
            return "Ошибка: коды валют не могут быть пустыми."

        if not isinstance(from_curr, str) or not isinstance(to_curr, str):
            return "Ошибка: коды валют должны быть строками."

        # Нормализация: верхний регистр, обрезка пробелов
        from_curr = from_curr.strip().upper()
        to_curr = to_curr.strip().upper()

        # Проверка формата кода (2–5 букв)
        if not (2 <= len(from_curr) <= 5) or not from_curr.isalpha():
            return f"Ошибка: некорректный код валюты '{from_curr}'. Должно быть 2–5 букв."
        if not (2 <= len(to_curr) <= 5) or not to_curr.isalpha():
            return f"Ошибка: некорректный код валюты '{to_curr}'. Должно быть 2–5 букв."

        # 2. Проверка существования валют в реестре
        try:
            get_currency(from_curr)
        except CurrencyNotFoundError:
            return (f"Ошибка: валюта '{from_curr}' не найдена. "
                   f"Используйте 'help get-rate' для списка поддерживаемых валют.")

        try:
            get_currency(to_curr)
        except CurrencyNotFoundError:
            return (f"Ошибка: валюта '{to_curr}' не найдена. "
                   f"Используйте 'help get-rate' для списка поддерживаемых валют.")

        # 3. Получение курса
        rate_service = RateService()
        result: Optional[Tuple[float, str]] = rate_service.get_rate(from_curr, to_curr)

        if result is None:
            return f"Курс {from_curr}→{to_curr} недоступен. Повторите попытку позже."

        rate, timestamp = result

        # 4. Форматирование вывода
        dt = datetime.fromisoformat(timestamp)
        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        reverse_rate = 1 / rate if rate != 0 else 0

        return (
            f"Курс {from_curr}→{to_curr}: {rate:.8f} (обновлено: {formatted_time})\n"
            f"Обратный курс {to_curr}→{from_curr}: {reverse_rate:.2f}"
        )

    except CurrencyNotFoundError as e:
        # Дополнительный обработчик на случай, если исключение проскочило выше
        return (f"Ошибка: {e}. "
               f"Используйте 'help get-rate' для списка поддерживаемых валют.")
    except Exception as e:
        # Ловим непредвиденные ошибки
        return f"Неожиданная ошибка: {str(e)}"

