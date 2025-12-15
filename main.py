import datetime
import re
from typing import Dict
import json

from valutatrade_hub.core.models import User, Wallet, Portfolio, ExchangeRates
from valutatrade_hub.core.usecases import register_user, login_user, show_portfolio, buy, sell,get_rate


# Пути к файлам данных
USERS_FILE = "users.json"
PORTFOLIOS_FILE = "portfolios.json"
RATES_FILE = "data/rates.json"

def main():
    """ main function """
    print("final_project")

    
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
                print(active_obj_portfolio)
                base_currency = input("Введите базовую валюту для операций: ").strip().upper()
                print(f"Установлена базовая валюта: {base_currency}")
                
            elif command.startswith('show-portfolio'):

                base = args.get('base', base_currency)  # по умолчанию USD
                show_portfolio(active_obj_user, active_obj_portfolio, er, base)
            
            elif command.startswith('buy'):
                
                amount = args.get('amount', None)
                currency = args.get('currency', None)
                portfolio = buy(active_obj_user, currency, amount, base_currency)
                active_obj_portfolio = portfolio
                
            elif command.startswith('sell'):
                
                amount = args.get('amount', None)
                currency = args.get('currency', None)
                portfolio = sell(active_obj_user, currency, amount, base_currency)               
                active_obj_portfolio = portfolio
                
            elif command.startswith('get-rate'):
                
                from_  = args.get('from', None)
                to_ = args.get('to', None)
                get_rate(from_, to_)
                
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
    from_match = re.search(r'--from\s+(\S+)', command)
    to_match = re.search(r'--to\s+(\S+)', command)
        


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
    if from_match:
        args['from'] = from_match.group(1)
    if to_match:
        args['to'] = to_match.group(1)

    return args
    
    
if __name__ == "__main__":
    main()
