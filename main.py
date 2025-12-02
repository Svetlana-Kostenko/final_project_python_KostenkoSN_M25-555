from valutatrade_hub.core.models import *

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
    
    
    
if __name__ == "__main__":
    main()
