from valutatrade_hub.core.models import *
from valutatrade_hub.core.usecases import *
import json
import hashlib
import datetime
import argparse
import os
from typing import Dict, Any
import re

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
    
    while True:
        try:
            # Получаем команду от пользователя
            command = input("> ").strip()

            if command.lower() == 'exit':
                print("До свидания!")
                break

            if not command.startswith('register'):
                print("Неизвестная команда. Используйте 'register --username <имя> --password <пароль>'")
                continue

            # Разбираем команду
            args = parse_command(command)

            if 'username' not in args:
                print("Ошибка: не указан --username")
                continue
            if 'password' not in args:
                print("Ошибка: не указан --password")
                continue

            # Регистрируем пользователя
            register_user(args['username'], args['password'])

        except KeyboardInterrupt:
            print("\nДо свидания!")
            break
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")


def parse_command(command: str) -> Dict[str, str]:
    """Разбирает командную строку и возвращает словарь параметров."""
    args = {}
    # Ищем --username и --password с помощью регулярных выражений
    username_match = re.search(r'--username\s+(\S+)', command)
    password_match = re.search(r'--password\s+(\S+)', command)

    if username_match:
        args['username'] = username_match.group(1)
    if password_match:
        args['password'] = password_match.group(1)

    return args
    
    
if __name__ == "__main__":
    main()
