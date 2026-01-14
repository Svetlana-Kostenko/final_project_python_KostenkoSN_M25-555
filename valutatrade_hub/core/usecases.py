import hashlib
from datetime import datetime, timezone
from typing import Dict
from valutatrade_hub.core.exceptions import InsufficientFundsError
from constants import PORTFOLIOS_FILE
from parse_service.config import config
from valutatrade_hub.core.models import User, Portfolio, Wallet
from parse_service.updater import rates_updates
from valutatrade_hub.core.utils import save_users, load_portfolios, save_portfolios, generate_salt



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


    # Генерируем user_id (автоинкремент)
    user_id = max(users.keys()) + 1 if users else 1

    # Генерируем соль и хешируем пароль
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


    users[user_id] = user

    # Сохраняем пользователей
    save_users(users)

    # Cоздаём пустой портфель
    portfolios = load_portfolios()
    currency = input("Введите валюту: ").strip().upper()
    amount = input("Введите баланс: ")
    
    try:
        if "." in amount:
            value = int(amount)
        else:
            value = float(amount)
    except (ValueError, TypeError):        
        raise TypeError("Баланс должен быть числом (int или float).")
    if value < 0:
            raise ValueError("Баланс не может быть отрицательным.")
    
    wallet_new_user = Wallet(currency, value)
    
    user_portfolio = Portfolio(user_id, {"USD":  wallet_new_user})
    portfolios.append(user_portfolio.to_dict())
    save_portfolios(portfolios)

    # Выводим сообщение об успехе
    print(f"Пользователь '{username}' зарегистрирован (id={user_id}). Войдите: login --username {username} --password ****")
    
    
    
def login_user(username: str, password: str):
    """Выполняет вход пользователя в систему."""
    users = User.load_users()
    portfolios = Portfolio.load_from_file(PORTFOLIOS_FILE)
    
    # Найти пользователя по username
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
    
    
    # Сравнить хеш пароля
    if user.verify_password(password):
        print(f"Вы вошли как '{username}'")
    else:
        raise ValueError("Неверный пароль")
    return user, portfolio
        
        
def show_portfolio(user: User, portfolio: Portfolio, er: Dict, base_currency: str):
    """
    Показывает портфель пользователя в заданной базовой валюте.
    """

    if not user:
        print("Сначала выполните login")
        return


    if not portfolio:
        print(f"Портфель пользователя '{user.username}' пуст")
        return


    # Проверить, что базовая валюта известна
    if base_currency not in er.exchange_rate_default:
        print(f"Неизвестная базовая валюта '{base_currency}'")
        return

   

    print(f"\nПортфель пользователя '{user.username}' (база: {base_currency}):")
    

    for code, wallet in  portfolio.wallets.items():
        rate = er.exchange_rate_default[code] / er.exchange_rate_default[base_currency]
        print(f"- {code}: {wallet.balance} -> {rate*wallet.balance} {base_currency}")

    total_in_base = portfolio.get_total_value(base_currency)


    # Bnоговая сумма
    print("-" * 40)
    print(f"ИТОГО: {total_in_base:.2f} {base_currency}\n")
    
    
def buy(user: User, currency: str, amount: float, base_currency: str = "USD"):
    
    """
     Команда покупки валюты.
     Аргументы
    - user: объект класса User
    - currency: код валюты (например, 'BTC')
    - amount: количество валюты для покупки (должно быть > 0)
    - base_currency: базовая валюта для расчёта стоимости (по умолчанию USD)
    
    return: строка с результатом выполнения команды
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

    # Валидировать аргументы
    if not isinstance(currency, str) or not currency.strip():
        raise ValueError("Ошибка: код валюты не может быть пустым.")
    
    currency = currency.strip().upper()
    amount = float(amount)
    
    if not isinstance(amount, (int, float)):
        raise ValueError("'amount' должен быть числом.")
    
    
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом.")

    
    # Проверить наличие кошелька, при отсутствии — создать
    try:
        if portfolio.get_wallet(currency) is None:
            portfolio.add_currency(currency)
    except ValueError as e:
        return f"Ошибка: {str(e)}"
        
    wallet_base_currency = portfolio.get_wallet(base_currency)
 
    # Получаем курс валюты к базовой
    if currency not in portfolio.EXCHANGE_RATES:
        raise KeyError(f"Курс для {currency} не найден.")
        
    if base_currency not in portfolio.EXCHANGE_RATES:
        raise KeyError(f"Базовая валюта {base_currency} не поддерживается.")
        
    rate = portfolio.EXCHANGE_RATES[currency] / portfolio.EXCHANGE_RATES[base_currency]
    cost = amount * rate
    current_balance =  wallet_base_currency.balance
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
    portfolios_as_dicts = [p.to_dict() if isinstance(p, Portfolio) else p for p in portfolios]
    save_portfolios(portfolios_as_dicts)
    
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

    # Валидировать аргументы
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
    portfolios_as_dicts = [p.to_dict() if isinstance(p, Portfolio) else p for p in portfolios]
    save_portfolios(portfolios_as_dicts)

    return portfolio
    
    
def get_rate(from_curr, to_curr, er) -> str:
    """
    Обрабатывает команду get-rate.
    args — список аргументов после имени команды (например, ["--from", "USD", "--to", "BTC"]).
    """

    # Bалидация кодов валют
    if not from_curr or not to_curr:
        return "Ошибка: коды валют не могут быть пустыми."
    if not from_curr.isalpha() or not to_curr.isalpha():
        return "Ошибка: коды валют должны содержать только буквы."

    from_curr = from_curr.upper()
    to_curr = to_curr.upper()

    rate = er.exchange_rate_default[from_curr]/er.exchange_rate_default[to_curr]

    reverse_rate = 1 / rate if rate != 0 else 0
    
    last_refresh_seconds_ago = (datetime.now(timezone.utc)-datetime.fromisoformat(er._last_refresh.replace('Z', '+00:00'))).total_seconds()
    print(
            f"Курс {from_curr}→{to_curr}: {rate} (обновлено: {er._last_refresh})\n"
            f"Обратный курс {to_curr}→{from_curr}: {reverse_rate}"
        )
    if last_refresh_seconds_ago >  config.CACHE_TTL:
        print("Данные устарели. Запускаю процесс обновления")
        rates_updates.run_update()
        rate = er.exchange_rate_default[from_curr]/er.exchange_rate_default[to_curr]
        reverse_rate = 1 / rate if rate != 0 else 0  
        print(
                f"Курс {from_curr}→{to_curr}: {rate} (обновлено: {er._last_refresh})\n"
                f"Обратный курс {to_curr}→{from_curr}: {reverse_rate}"
        
        )

