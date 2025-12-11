import datetime
import re
from typing import Dict

from valutatrade_hub.core.models import User, Wallet, Portfolio, ExchangeRates
from valutatrade_hub.core.usecases import register_user, login_user, show_portfolio, buy, sell


# Пути к файлам данных
USERS_FILE = "users.json"
PORTFOLIOS_FILE = "portfolios.json"

def main():
    """ main function """
    print("final_project")
    # Создание пользователя
    user = User(
        user_id=1,
        username="alice",
        hashed_password="",  # изначально пустой
        salt="x5T9!",
        registration_date=datetime.datetime(2025, 10, 9, 12, 0, 0)
    )


    print(user.get_user_info())
    # Создание кошелька
    wallet = Wallet(currency_code="BTC", balance=0.05)

    # Пополнение
    wallet.deposit(0.01)
    print(wallet.get_balance_info())  # {'currency_code': 'BTC', 'balance': 0.06}

    # Снятие (успешно)
    success = wallet.withdraw(0.02)
    print(success)  # True
    print(wallet.balance)  # 0.04

    # Снятие (недостаточно средств)
    success = wallet.withdraw(1.0)
    print(success)  # False

    # Создание портфеля
    portfolio = Portfolio(user_id=1)

    # Добавление кошельков
    portfolio.add_currency("USD")
    portfolio.add_currency("EUR")
    portfolio.add_currency("BTC")

    # Пополнение кошельков
    usd_wallet = portfolio.get_wallet("USD")
    usd_wallet.deposit(1500.0)

    eur_wallet = portfolio.get_wallet("EUR")
    eur_wallet.deposit(200.0)

    btc_wallet = portfolio.get_wallet("BTC")
    btc_wallet.deposit(0.05)

    # Общая стоимость в USD
    total_usd = portfolio.get_total_value("USD")
    print(f"Общая стоимость: {total_usd:.2f} USD")  # ~4000 USD
    print(portfolio.to_dict())
    
    print("Консольная система аутентификации")
    print("Доступные команды:")
    print("  register --username <имя> --password <пароль> — регистрация")
    print("  login --username <имя> --password <пароль> — вход в систему")
    print("  exit — выход")
    print()
    
    active_obj_user = None
    active_obj_portfolio = None
    base_currency = None
    er = ExchangeRates()
    print (er.exchange_rate_default)
    
    
    while True:
        
        try:
            command = input("> ").strip()
            if command.lower() == 'exit':
                print("До свидания!")
                break

            if not command:
                continue

            args = parse_command(command)

            if command.startswith('register'):
                if 'username' not in args:
                    print("Ошибка: не указан --username")
                    continue
                if 'password' not in args:
                    print("Ошибка: не указан --password")
                    continue
                register_user(args['username'], args['password'])

            elif command.startswith('login'):
                if 'username' not in args:
                    print("Ошибка: не указан --username")
                    continue
                if 'password' not in args:
                    print("Ошибка: не указан --password")
                    continue
                active_obj_user, active_obj_portfolio = login_user(args['username'], args['password'])
                base_currency = input("Введите базовую валюту для операций: ").upper()
                print(f"Установлена базовая валюта: {base_currency}")
                
            elif command.startswith('show-portfolio'):

                base = args.get('base', base_currency)  # по умолчанию USD
                show_portfolio(active_obj_user, active_obj_portfolio, er, base)
            
            elif command.startswith('buy'):
                
                amount = args.get('amount', None)
                buy(active_obj_user, currency, amount, base_currency)
                
            elif command.startswith('sell'):
                
                amount = args.get('amount', None)
                sell(active_obj_user, currency, amount, base_currency)
                
            elif command.startswith('logout'):
                active_obj_user = None
                active_obj_portfolio = None
                base_currency = None
                
                print("Сессия завершена")
                
                
            
            else:
                print("Неизвестная команда. Используйте register или login.")

        except KeyboardInterrupt:
            print("\nДо свидания!")
            break
        except Exception as e:
            print(e)


def parse_command(command: str) -> Dict[str, str]:
    """Разбирает командную строку и возвращает словарь параметров."""
    args = {}
    # Ищем --username и --password с помощью регулярных выражений
    username_match = re.search(r'--username\s+(\S+)', command)
    password_match = re.search(r'--password\s+(\S+)', command)
    base_match = re.search(r'--base\s+(\S+)', command)
    currency_match = re.search(r'--currency\s+(\S+)', command)
    amount_match = re.search(r'--amount\s+(\S+)', command)


    if username_match:
        args['username'] = username_match.group(1)
    if password_match:
        args['password'] = password_match.group(1)
    if base_match:
        args['base'] = base_match.group(1)
    if currency_match:
        args['currency'] = currency_match.group(1)
    if amount_match:
        args['amount'] = amount_match.group(1)

    return args
    
    
if __name__ == "__main__":
    main()
