import requests
from abc import ABC, abstractmethod
from typing import Dict
from parse_service.config import config  # Импортируем конфигурацию
import time
import hashlib
from datetime import datetime

class ApiRequestError(Exception):
    """Исключение для ошибок при запросах к API."""
    pass

class BaseApiClient(ABC):
    """Абстрактный базовый класс для клиентов внешних API."""
    
    def __init__(self):
        self._source = None  # Или raise NotImplementedError

    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """Получить курсы валют в стандартизированном формате."""
        pass
        

    @property
    def source(self) -> str:
        return self._source

class CoinGeckoClient(BaseApiClient):
    """Клиент для работы с API CoinGecko."""

    def __init__(self):
        self.url = config.COINGECKO_URL
        self.timeout = config.REQUEST_TIMEOUT
        self._source = "CoinGecko"

    def fetch_rates(self) -> Dict[str, float]:
 
        ids = ",".join(config.CRYPTO_ID_MAP.values())                    
        params = {
                "ids": ids,
                "vs_currencies": config.BASE_CURRENCY.lower()
            }
            
        start_time = time.time()
            
        try:
            response = requests.get(self.url, params=params, timeout=config.REQUEST_TIMEOUT)
            request_ms = int((time.time() - start_time) * 1000)
            status_code = response.status_code
            etag = response.headers.get("ETag", "")
            response.raise_for_status()         
            data = response.json()
            timestamp = datetime.now().isoformat()

            result = []
            for code, cg_id in config.CRYPTO_ID_MAP.items():
                if cg_id in data:
                    rate = data[cg_id][config.BASE_CURRENCY.lower()]
                    temp = {
                        "from_currency": code,
                        "to_currency": config.BASE_CURRENCY,
                        "rate": rate,  
                        "timestamp": timestamp,
                        "source": self._source,
                        "meta": {
                            "raw_id": cg_id,
                            "request_ms": request_ms,
                            "status_code": status_code,
                            "etag": etag or f"W/\"{hashlib.md5(response.text.encode()).hexdigest()[:6]}\""

                        }
                    }
                    result.append(temp)
                else:
                    print(f"Данные для {cg_id} не найдены")
                
            return result
                
        except requests.exceptions.RequestException as e:
            print(f"Ошибка запроса к API: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON: {e}")
            return []            
        except Exceptionas as e:
                print(e)



class ExchangeRateApiClient(BaseApiClient):
    """Клиент для работы с API ExchangeRate."""

    def __init__(self):
        self.timeout = config.REQUEST_TIMEOUT
        self._source = "ExchangeRate-API"
        self._url = config.EXCHANGERATE_API_URL

    def fetch_rates(self) -> Dict[str, float]:
        start_time = time.time()
        try:
            response = requests.get(self._url, timeout=self.timeout)
            request_ms = int((time.time() - start_time) * 1000)
            status_code = response.status_code
            etag = response.headers.get("ETag", "")
            data = response.json()
            
            if data.get("result") != "success":
                print(f"Ошибка API: {data.get('result')}")
                return []
            
            
            rates = []
            timestamp = datetime.now().isoformat()

            for from_currency, rate in data['conversion_rates'].items():
                temp = {"from_currency": from_currency,
                        "to_currency": config.BASE_CURRENCY,
                        "rate": 1 / rate,
                        "timestamp": timestamp,
                        "source":self._source,
                        "meta": {"raw_id": from_currency,
                                "request_ms": request_ms,
                                "status_code": status_code,
                                "etag": etag or f"W/\"{hashlib.md5(response.text.encode()).hexdigest()[:5]}\""
                        }
                }
                rates.append(temp)

            return rates

        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"Ошибка при запросе к ExchangeRate: {e}") from e            
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON: {e}")
            return []            
        except Exceptionas as e:
                print(e)

