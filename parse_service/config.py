import os
from dataclasses import dataclass, field
from dotenv import load_dotenv
from constants import RATES_FILE, HISTORY_RATES_FILE

load_dotenv()

@dataclass
class ParserConfig:
    # Ключ загружается из переменной окружения
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")


    # Списки валют
    BASE_CURRENCY: str = "USD"
    #FIAT_CURRENCIES: tuple = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES: tuple = ("BTC", "ETH", "SOL")
    CRYPTO_ID_MAP: dict = field(
        default_factory=lambda: {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana"
            }
    )
    
    # Время жизни кеша (5 минут)
    CACHE_TTL = 300  
    
    # Эндпоинты
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/latest/{BASE_CURRENCY}"

    # Пути
    RATES_FILE_PATH: str = RATES_FILE
    HISTORY_FILE_PATH: str = HISTORY_RATES_FILE

    # Сетевые параметры
    REQUEST_TIMEOUT: int = 10 
    
config = ParserConfig()
