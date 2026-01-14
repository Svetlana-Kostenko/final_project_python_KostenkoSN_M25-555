from datetime import datetime
from typing import List, Dict, Any
from parse_service.api_clients import BaseApiClient, CoinGeckoClient, ExchangeRateApiClient
import json
import os
from constants import RATES_FILE, HISTORY_RATES_FILE

CG = CoinGeckoClient()
ER_api = ExchangeRateApiClient()
clients_lst = [CG, ER_api]

def load_rates_as_dict(json_file: str) -> Dict[str, float]:
    """
    Читает файл rates.json и возвращает словарь {пара: rate}.

    Args:
        json_file: путь к JSON‑файлу.

    Returns:
        Словарь
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Извлекаем пары и их rates
        rates_dict = {}
        for pair_key, pair_info in data['pairs'].items():
            rates_dict[pair_key] = pair_info['rate']

        return rates_dict, data['last_refresh']

    except FileNotFoundError:
        print(f"Файл {json_file} не найден.")
        return {}
    except KeyError as e:
        print(f"Ошибка: отсутствует ключ {e} в JSON.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON: {e}")
        return {}
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return {}


def append_exchange_rates(data: List[Dict[str, Any]], output_file: str = HISTORY_RATES_FILE) -> None:
    # Читаем существующие данные (если файл есть)
    existing_records = []
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_records = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Предупреждение: не удалось прочитать существующий файл {output_file}: {e}")
            existing_records = []

    # Обрабатываем новые записи
    new_records = []
    for record in data:
        # Валидация обязательных полей
        required_fields = {'from_currency', 'to_currency', 'rate', 'timestamp', 'source', 'meta'}
        if not all(field in record for field in required_fields):
            print(f"Пропускаем запись: отсутствуют обязательные поля — {record}")
            continue

        # Проверка типов
        if not isinstance(record['rate'], (int, float)) or record['rate'] < 0:
            print(f"Пропускаем запись: некорректный rate — {record}")
            continue
        if not isinstance(record['timestamp'], str):
            print(f"Пропускаем запись: timestamp не строка — {record}")
            continue

        # Нормализация: коды валют в верхний регистр
        from_curr = record['from_currency'].upper()
        to_curr = record['to_currency'].upper()

        # Формирование id
        clean_timestamp = record['timestamp'].split('.')[0] + 'Z'
        record_id = f"{from_curr}_{to_curr}_{clean_timestamp}"

        # Сборка итоговой записи
        processed_record = {
            "id": record_id,
            "from_currency": from_curr,
            "to_currency": to_curr,
            "rate": record['rate'],
            "timestamp": clean_timestamp,
            "source": record['source'],
            "meta": record['meta']
        }
        new_records.append(processed_record)

    # Объединяем существующие и новые записи
    all_records = existing_records + new_records

    # Атомарная запись: временный файл → rename
    temp_file = output_file + ".tmp"
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(all_records, f, ensure_ascii=False, indent=2)
        # Атомарное переименование
        os.replace(temp_file, output_file)
        print(f"Успешно добавлено {len(new_records)} новых записей (всего {len(all_records)} в {output_file})")
    except Exception as e:
        print(f"Ошибка при записи файла: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)


def save_rates_as_pairs(
    data: List[Dict[str, Any]],
    output_file: str = RATES_FILE,
    last_refresh: str = None
) -> None:
    """
    Сохраняет курсы валют 

    Args:
        data: список словарей с данными о курсах.
        output_file: путь к выходному файлу.
        last_refresh: timestamp для поля last_refresh (если None — берётся сейчас).
    """
    # Валидация и нормализация входных данных
    valid_records = []
    for record in data:
        # Проверка обязательных полей
        required_fields = {'from_currency', 'to_currency', 'rate', 'timestamp', 'source'}
        if not all(field in record for field in required_fields):
            print(f"Пропускаем запись: отсутствуют обязательные поля — {record}")
            continue

        # Проверка типов
        if not isinstance(record['rate'], (int, float)) or record['rate'] < 0:
            print(f"Пропускаем запись: некорректный rate — {record}")
            continue
        if not isinstance(record['timestamp'], str):
            print(f"Пропускаем запись: timestamp не строка — {record}")
            continue

        # Нормализация: валюты в верхний регистр
        from_curr = record['from_currency'].upper()

        # Очистка timestamp (убираем микросекунды, добавляем Z)
        clean_timestamp = record['timestamp'].split('.')[0] + 'Z'

        # Формирование ключа пары
        pair_key = f"{from_curr}"

        valid_records.append({
            "pair": pair_key,
            "rate": record['rate'],
            "updated_at": clean_timestamp,
            "source": record['source']
        })

    # Сбор актуальных записей (по свежему updated_at)
    pairs = {}
    for record in valid_records:
        pair_key = record["pair"]
        # Если пары ещё нет или новая запись свежее — обновляем
        if pair_key not in pairs or record["updated_at"] > pairs[pair_key]["updated_at"]:
            pairs[pair_key] = {
                "rate": record["rate"],
                "updated_at": record["updated_at"],
                "source": record["source"]
            }

    # Формирование итогового объекта
    result = {
        "pairs": pairs,
        "last_refresh": last_refresh or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }

    # Атомарная запись: временный файл → rename
    temp_file = output_file + ".tmp"
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, output_file)
        
            
        er.exchange_rate_default, er.last_refresh = {pair_key: pair_info['rate'] for pair_key, pair_info in result['pairs'].items()},  result["last_refresh"]
        print(f"Успешно сохранено {len(pairs)} пар в {output_file}")

    except Exception as e:
        print(f"Ошибка при записи файла: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
class RatesUpdater:
    """
    Координирует процесс обновления курсов валют:
    - опрашивает API‑клиенты;
    - объединяет данные;
    - добавляет метаданные;
    - сохраняет в хранилище.
    """

    def __init__(self, clients: List[BaseApiClient]):
        """
        Args:
            clients: список экземпляров API‑клиентов.
            storage: экземпляр хранилища для сохранения данных.
        """
        self.clients = clients

    def run_update(self) -> None:
        """
        Основной метод: выполняет полный цикл обновления.
        """
        all_rates = []


        # Вызываем fetch_rates() у каждого клиента
        for client in self.clients:
            try:
                rates = client.fetch_rates()
                all_rates += rates
                
            except Exception as e:
                print(f"Клиент {client.source} упал, {e}")
                


        append_exchange_rates(all_rates)
        save_rates_as_pairs(all_rates)

class ExchangeRates:
    _instance = None  # Для синглтон‑паттерна

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Инициализация при первом создании
            cls._instance._exchange_rate_default, cls._instance._last_refresh = load_rates_as_dict(RATES_FILE)
        return cls._instance

    @property
    def exchange_rate_default(self) -> dict:
        """Геттер для словаря курсов валют."""
        return self._exchange_rate_default

    @exchange_rate_default.setter
    def exchange_rate_default(self, value: dict) -> None:
        """Сеттер для словаря курсов валют."""
        if not isinstance(value, dict):
            raise TypeError("exchange_rate_default должен быть словарем")
        self._exchange_rate_default = value

    @property
    def last_refresh(self) -> str:
        """Геттер для времени последнего обновления."""
        return self._last_refresh

    @last_refresh.setter
    def last_refresh(self, value: str) -> None:
        """Сеттер для времени последнего обновления."""
        if not isinstance(value, str):
            raise TypeError("last_refresh должен быть строкой в формате ISO 8601")
        self._last_refresh = value

er = ExchangeRates()
rates_updates = RatesUpdater(clients_lst)
