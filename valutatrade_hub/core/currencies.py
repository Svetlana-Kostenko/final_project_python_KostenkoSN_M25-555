from abc import ABC, abstractmethod
from typing import Dict
from valutatrade_hub.core.exceptions import CurrencyNotFoundError

class Currency(ABC):
    """
    Абстрактный базовый класс для всех типов валют.
    """
    
    def __init__(self, name: str, code: str):
        # Валидация атрибутов
        if not name or not isinstance(name, str):
            raise ValueError("name должен быть непустой строкой")
        if (not code or not isinstance(code, str) or 
                not (2 <= len(code) <= 5) or ' ' in code):
            raise ValueError("code должен быть строкой 2–5 символов без пробелов")
        
        self.name: str = name
        self.code: str = code.upper()
    
    @abstractmethod
    def get_display_info(self) -> str:
        """Возвращает строковое представление для UI/логов."""
        pass


class FiatCurrency(Currency):
    """
    Валюта фиатного типа (государственная/банковская).
    """
    
    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        if not issuing_country or not isinstance(issuing_country, str):
            raise ValueError("issuing_country должен быть непустой строкой")
        self.issuing_country: str = issuing_country
    
    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"



class CryptoCurrency(Currency):
    """
    Криптовалюта.
    """
    
    def __init__(self, name: str, code: str, algorithm: str, market_cap: float):
        super().__init__(name, code)
        if not algorithm or not isinstance(algorithm, str):
            raise ValueError("algorithm должен быть непустой строкой")
        if market_cap < 0:
            raise ValueError("market_cap должен быть неотрицательным числом")
        self.algorithm: str = algorithm
        self.market_cap: float = market_cap
    
    def get_display_info(self) -> str:
        # Форматируем капитализацию в экспоненциальной нотации (1.12e12)
        mcap_str = f"{self.market_cap:.2e}"
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {mcap_str})"






# Реестр валют (глобальный словарь)
_CURRENCY_REGISTRY: Dict[str, Currency] = {}

def register_currency(currency: Currency):
    """Добавляет валюту в реестр."""
    _CURRENCY_REGISTRY[currency.code] = currency


    
def get_currency(code: str) -> Currency:
    """
    Возвращает экземпляр валюты по коду.
    
    Args:
        code: код валюты (строка, например 'USD', 'BTC')
    
    Returns:
        Экземпляр Currency, соответствующий указанному коду
    
    Raises:
        TypeError: если code не является строкой
        ValueError: если code пустой или содержит недопустимые символы
        CurrencyNotFoundError: если валюта с указанным кодом не найдена в реестре
    
    """
    # Валидация входного параметра
    if not isinstance(code, str):
        raise TypeError("Код валюты должен быть строкой")
    
    if not code or not code.strip():
        raise ValueError("Код валюты не может быть пустым или состоять только из пробелов")
    
    
    # Нормализация кода (верхний регистр, удаление лишних пробелов)
    code = code.strip().upper()
    
    # Дополнительная проверка формата кода (2–5 букв)
    if not (2 <= len(code) <= 5) or not code.isalpha():
        raise ValueError(
            "Код валюты должен содержать от 2 до 5 букв латинского алфавита"
        )
    
    # Поиск в реестре
    if code not in _CURRENCY_REGISTRY:
        raise CurrencyNotFoundError(code)
    
    return _CURRENCY_REGISTRY[code]

