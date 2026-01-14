from parse_service.api_clients import CoinGeckoClient, ExchangeRateApiClient
from valutatrade_hub.cli.interface import main

CG = CoinGeckoClient()
ER = ExchangeRateApiClient()
clients_lst = [CG, ER]


   
    
if __name__ == "__main__":
    main()
