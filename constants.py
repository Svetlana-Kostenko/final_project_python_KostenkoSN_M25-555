USERS_FILE = "data/users.json"
PORTFOLIOS_FILE = "data/portfolios.json"
RATES_FILE = "data/rates.json"
HISTORY_RATES_FILE: str = "data/exchange_rates.json"
    
HELP_TEXT = """   
    Доступные команды:
      register --username <имя> --password <пароль> — регистрация
      login --username <имя> --password <пароль> — вход в систему
      show-portfolio --base <валюта> (опционально) — показать все кошельки и итоговую стоимость в базовой валюте (по умолчанию USD)
      buy --currency <валюта> --amount <число> — купить валюту
      sell --currency <валюта> --amount <число> — продать валюту
      get-rate  --from <валюта> --to <валюта> — получить текущий курс одной валюты к другой
      help — справка
      exit — выход
    
    """
