class InsufficientFundsError(Exception):
    """
    Возникает при попытке снять/продать больше средств, чем есть на кошельке.
    """
    def __init__(self, available: float, required: float, code: str):
        self.available = available
        self.required = required
        self.code = code
        super().__init__(
            f"Недостаточно средств: доступно {available:.8f} {code}, требуется {required:.8f} {code}"
        )



class CurrencyNotFoundError(Exception):
    """
    Возникает, когда валюта с указанным кодом не найдена в реестре.
    """
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Неизвестная валюта '{code}'")



class ApiRequestError(Exception):
    """
    Возникает при ошибке взаимодействия с внешним API (сеть, тайм‑аут, 5xx и т. п.).
    """
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")

