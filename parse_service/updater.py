from datetime import datetime
from typing import List, Dict, Any
from parse_service.api_clients import BaseApiClient, CoinGeckoClient, ExchangeRateApiClient

CG = CoinGeckoClient()
ER = ExchangeRateApiClient()
clients_lst = [CG, ER]


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
        success_count = 0
        fail_count = 0

        # 1. Вызываем fetch_rates() у каждого клиента
        for client in self.clients:
            try:
                rates = client.fetch_rates()
                print("rates", rates)
                all_rates += rates
                
            except Exception:
                print(f"Клиент {client.source} упал")
                

        # 4. Передаём итоговый объект в storage для сохранения
        #self.storage.save(all_rates)
        print(all_rates)


