import hashlib
import datetime
import json
from typing import Optional



class User:
    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime.datetime
    ):
        # Приватные атрибуты
        self._user_id = user_id
        self._username = self._validate_username(username)
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    # Геттеры
    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime.datetime:
        return self._registration_date

    # Сеттеры с проверками
    @username.setter
    def username(self, value: str):
        self._username = self._validate_username(value)

    def _validate_username(self, username: str) -> str:
        if not username or not username.strip():
            raise ValueError("Имя пользователя не может быть пустым.")
        return username.strip()

    def get_user_info(self) -> dict:
        """Возвращает информацию о пользователе без пароля."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat()
        }

    def change_password(self, new_password: str):
        """Изменяет пароль пользователя, хешируя новый пароль с солью."""
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов.")

        # Формируем новый хеш: пароль + соль
        password_salt = new_password + self._salt
        hashed = hashlib.sha256(password_salt.encode()).hexdigest()

        self._hashed_password = hashed

    def verify_password(self, password: str) -> bool:
        """Проверяет введённый пароль на совпадение."""
        if len(password) < 4:
            return False

        # Сравниваем хеш введённого пароля с сохранённым
        password_salt = password + self._salt
        hashed = hashlib.sha256(password_salt.encode()).hexdigest()

        return hashed == self._hashed_password

    def to_dict(self) -> dict:
        """Преобразует объект в словарь для сохранения в JSON."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Создаёт объект User из словаря (например, из JSON)."""
        registration_date = datetime.datetime.fromisoformat(data["registration_date"])
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            hashed_password=data["hashed_password"],
            salt=data["salt"],
            registration_date=registration_date
        )


import json
from typing import Dict



class Wallet:
    """Кошелёк пользователя для одной конкретной валюты."""

    def __init__(self, currency_code: str, balance: float = 0.0):
        self._currency_code = currency_code.upper()
        self._balance = balance

    @property
    def currency_code(self) -> str:
        """Геттер для кода валюты (только чтение)."""
        return self._currency_code

    @property
    def balance(self) -> float:
        """Геттер для баланса."""
        return self._balance

    @balance.setter
    def balance(self, value: float):
        """Сеттер для баланса с валидацией."""
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом (int или float).")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным.")
        self._balance = float(value)

    def deposit(self, amount: float) -> None:
        """Пополнение баланса."""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма пополнения должна быть числом (int или float).")
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной.")
        
        self._balance += amount

    def withdraw(self, amount: float) -> bool:
        """
        Снятие средств.
        Возвращает True, если операция успешна, False — если недостаточно средств.
        """
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма снятия должна быть числом (int или float).")
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной.")
        if self._balance < amount:
            return False  # Недостаточно средств
        
        self._balance -= amount
        return True

    def get_balance_info(self) -> Dict[str, float]:
        """Возвращает информацию о текущем балансе в виде словаря."""
        return {
            "currency_code": self._currency_code,
            "balance": self._balance
        }

    def to_dict(self) -> Dict:
        """Преобразует объект в словарь для сохранения в JSON."""
        return self.get_balance_info()

    @classmethod
    def from_dict(cls, data: Dict):
        """Создаёт объект Wallet из словаря (например, из JSON)."""
        return cls(
            currency_code=data["currency_code"],
            balance=data["balance"]
        )
        
        
import json
from typing import Dict, Optional



class Portfolio:
    """Портфель пользователя: управление кошельками в разных валютах."""

    # Фиксированные курсы для упрощения (в реальной системе — API)
    EXCHANGE_RATES = {
        "USD": 1.0,
        "EUR": 1.1,    # 1 EUR = 1.1 USD
        "BTC": 50000, # 1 BTC = 50 000 USD
        "GBP": 1.3,
        "JPY": 0.007
    }

    def __init__(self, user_id: int, wallets: Optional[Dict[str, Wallet]] = None):
        """
        Инициализация портфеля.
        :param user_id: уникальный ID пользователя
        :param wallets: словарь кошельков (по умолчанию пустой)
        """
        self._user_id = user_id
        self._wallets: Dict[str, Wallet] = wallets or {}

    @property
    def user(self) -> int:
        """Геттер для user_id (только чтение)."""
        return self._user_id

    @property
    def wallets(self) -> Dict[str, Wallet]:
        """
        Геттер: возвращает копию словаря кошельков.
        Предотвращает прямое изменение внутреннего состояния.
        """
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> None:
        """
        Добавляет новый кошелёк в портфель, если его ещё нет.
        :param currency_code: код валюты (например, "USD", "BTC")
        :raises ValueError: если валюта уже есть или не поддерживается
        """
        currency_code = currency_code.upper()

        # Проверка на существование кошелька
        if currency_code in self._wallets:
            raise ValueError(f"Кошелёк для валюты {currency_code} уже существует в портфеле.")

        # Проверка поддержки валюты
        if currency_code not in self.EXCHANGE_RATES:
            raise ValueError(
                f"Валюта {currency_code} не поддерживается. "
                f"Доступные валюты: {list(self.EXCHANGE_RATES.keys())}"
            )

        # Создание нового кошелька с нулевым балансом
        self._wallets[currency_code] = Wallet(currency_code=currency_code, balance=0.0)

    def get_wallet(self, currency_code: str) -> Optional[Wallet]:
        """
        Возвращает объект Wallet по коду валюты.
        :param currency_code: код валюты
        :return: объект Wallet или None, если не найден
        """
        return self._wallets.get(currency_code.upper())

    def get_total_value(self, base_currency: str = "USD") -> float:
        """
        Возвращает общую стоимость всех валют в указанной базовой валюте.
        :param base_currency: код базовой валюты (по умолчанию USD)
        :return: общая стоимость в базовой валюте
        :raises ValueError: если базовая валюта не поддерживается
        """
        base_currency = base_currency.upper()

        if base_currency not in self.EXCHANGE_RATES:
            raise ValueError(f"Базовая валюта {base_currency} не поддерживается.")

        total = 0.0
        for currency, wallet in self._wallets.items():
            if currency in self.EXCHANGE_RATES:
                # Конвертация баланса в базовую валюту
                rate_to_base = self.EXCHANGE_RATES[currency] / self.EXCHANGE_RATES[base_currency]
                total += wallet.balance * rate_to_base
            else:
                # Валюта без курса — игнорируем (можно добавить логирование)
                pass

        return total

    def to_dict(self) -> Dict:
        """
        Преобразует портфель в словарь для сохранения в JSON.
        :return: словарь с данными портфеля
        """
        return {
            "user_id": self._user_id,
            "wallets": {
                code: wallet.to_dict() for code, wallet in self._wallets.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict):
        """
        Создаёт объект Portfolio из словаря (например, из JSON).
        :param data: словарь с данными портфеля
        :return: экземпляр Portfolio
        """
        wallets = {
            code: Wallet.from_dict(wallet_data)
            for code, wallet_data in data["wallets"].items()
        }
        return cls(user_id=data["user_id"], wallets=wallets)

