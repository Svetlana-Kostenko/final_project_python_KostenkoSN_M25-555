import hashlib
import json
import os
from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta
from valutatrade_hub.core.exceptions import InsufficientFundsError
from constants import USERS_FILE, RATES_FILE
from parse_service.updater import er


# Время жизни кеша (5 минут)
CACHE_TTL = 300  # секунд


class User:
    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime
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
    def registration_date(self) -> datetime:
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
        registration_date = datetime.fromisoformat(data["registration_date"])
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            hashed_password=data["hashed_password"],
            salt=data["salt"],
            registration_date=registration_date
        )
    @classmethod    
    def load_users(cls):
        """Загружает пользователей из users.json."""
        if not os.path.exists(USERS_FILE):
            return {}
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {user["user_id"]: cls.from_dict(user) for user in data}
        
    @classmethod
    def save_users(cls, users: Dict):
        """Сохраняет пользователей в users.json."""
        data = [user.to_dict() for user in users.values()]
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)



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
            raise InsufficientFundsError(
                available=self._balance,
                required=amount,
                code=self.currency_code
            )
            
        
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
        return {self._currency_code: {"balance": self._balance}}

    @classmethod
    def from_dict(cls, data: Dict):
        """Создаёт объект Wallet из словаря (например, из JSON)."""
        return cls(
            currency_code=data["currency_code"],
            balance=data["balance"]
        )
        
        




class Portfolio:
    """Портфель пользователя: управление кошельками в разных валютах."""



    def __init__(self, user_id: int, wallets: Optional[Dict[str, Wallet]] = None):
        """
        Инициализация портфеля.
        :param user_id: уникальный ID пользователя
        :param wallets: словарь кошельков (по умолчанию пустой)
        """
        self._user_id = user_id
        self._wallets: Dict[str, Wallet] = wallets or {}
        self.EXCHANGE_RATES = er.exchange_rate_default
        #{
     #           "USD_USD": 1.0,
     #           "EUR_USD": 1.1,    # 1 EUR = 1.1 USD
     #           "BTC_USD": 50000, # 1 BTC = 50 000 USD
      #          "GBP_USD": 1.3,
      #          "JPY_USD": 0.007
      #      }

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
        return self._wallets.get(currency_code.upper(), None)

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
            "wallets": 
                {currency: {"balance": wallet.balance} for currency, wallet in self._wallets.items()}
            
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
        
    @classmethod
    def from_json(cls, data: Dict[str, Any]):
        """
        Создаёт объект Portfolio из словаря (например, из JSON).
        """
        user_id = data["user_id"]
        
        # Преобразуем wallets: ключи — валюты, значения — балансы
        wallets = {}
        for currency, balance in data.get("wallets", {}).items():
            wallets[currency] = Wallet(currency_code=currency, balance=balance)
        
        return cls(user_id=user_id, wallets=wallets)

    @classmethod
    def load_from_file(cls, filename: str) -> list:
        """
        Загружает список портфелей из JSON‑файла.
        Поддерживает формат:
        [
          {
            "user_id": 1,
            "wallets": {
              "USD": {"balance": 1500.0},
              "BTC": {"balance": 0.05}
            }
          }
        ]
        """
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)  # data — список словарей
            
            portfolios = []
            for item in data:
                # Проверяем наличие обязательных полей
                if "user_id" not in item or "wallets" not in item:
                    raise ValueError(f"Некорректный формат записи в файле: {item}")
                
                user_id = item["user_id"]
                wallets_data = item["wallets"]
                
                # Создаём кошельки из вложенной структуры
                wallets = {}
                for currency, wallet_info in wallets_data.items():
                    if "balance" not in wallet_info:
                        raise ValueError(f"В кошельке {currency} отсутствует поле 'balance'")
                    balance = wallet_info["balance"]
                    wallets[currency] = Wallet(currency_code=currency, balance=balance)
                
                # Создаём портфель
                portfolio = cls(user_id=user_id, wallets=wallets)
                portfolios.append(portfolio)
            
            return portfolios

        except FileNotFoundError:
            print(f"Файл {filename} не найден. Создаётся пустой список портфелей.")
            return []
        except json.JSONDecodeError as e:
            print(f"Ошибка чтения JSON из файла {filename}: {e}")
            return []
        except Exception as e:
            print(f"Неожиданная ошибка при загрузке портфелей: {e}")
            return []
            
            
class RateService:
    @staticmethod
    def load_cache() -> Dict[str, Dict[str, float]]:
        """Загружает кеш из файла. Возвращает пустой dict при ошибке."""
        try:
            with open(RATES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @staticmethod
    def save_cache(data: Dict[str, Dict[str, float]]):
        """Сохраняет кеш в файл."""
        with open(RATES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def is_cache_fresh(timestamp_str: str) -> bool:
        """Проверяет, что метка времени в кеше моложе CACHE_TTL."""
        try:
            cached_time = datetime.fromisoformat(timestamp_str)
            return datetime.now() - cached_time < timedelta(seconds=CACHE_TTL)
        except ValueError:
            return False

    @classmethod
    def get_rate(cls, from_curr: str, to_curr: str) -> Optional[Tuple[float, str]]:
        """
        Возвращает курс from_curr → to_curr и метку времени.
        Если кеш устарел или отсутствует — запрашивает новые данные.
        """
        # Нормализуем коды
        from_curr = from_curr.upper()
        to_curr = to_curr.upper()

        # Загружаем кеш
        cache = cls.load_cache()
        print(cache)

        # Проверяем, есть ли свежий курс в кеше
        if (from_curr in cache and to_curr in cache[from_curr] and
                cls.is_cache_fresh(cache[from_curr]["timestamp"])):
            rate = cache[from_curr][to_curr]
            timestamp = cache[from_curr]["timestamp"]
            return rate, timestamp

        # Если кеш устарел или отсутствует — запрашиваем новые данные (заглушка)
        try:
            # Здесь должен быть вызов Parser Service
            # Для примера используем заглушку:
            new_rate = cls._fetch_rate_from_parser(from_curr, to_curr)
            if new_rate is None:
                return None

            # Обновляем кеш
            timestamp = datetime.now().isoformat()
            if from_curr not in cache:
                cache[from_curr] = {}
            cache[from_curr][to_curr] = new_rate
            cache[from_curr]["timestamp"] = timestamp
            cls.save_cache(cache)

            return new_rate, timestamp

        except Exception:
            return None

    @staticmethod
    def _fetch_rate_from_parser(from_curr: str, to_curr: str) -> Optional[float]:
        """
        Заглушка для вызова Parser Service.
        В реальной реализации здесь HTTP‑запрос к API.
        """
        # Пример: фиксированные курсы для демонстрации
        mock_rates = {
            ("USD", "BTC"): 0.00001685,
            ("BTC", "USD"): 59337.21,
            ("EUR", "USD"): 1.11,
            # ... другие пары
        }
        return mock_rates.get((from_curr, to_curr))

