import json
import os
from typing import Any, Optional

class SettingsLoader:
    _instance = None  # Хранилище единственного экземпляра

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False  # Флаг инициализации
        return cls._instance

    def __init__(self):
        # Инициализируем только один раз
        if self._initialized:
            return

        self._settings = {}
        self._config_path = None
        self._initialized = True

    def load(self, config_path: str) -> None:
        """
        Загружает конфигурацию из файла.
        Поддерживает JSON и TOML (если установлен toml).
        """
        self._config_path = config_path

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Конфигурационный файл не найден: {config_path}")

        try:
            if config_path.endswith(".toml"):
                import toml
                with open(config_path, "r", encoding="utf-8") as f:
                    self._settings = toml.load(f)
            elif config_path.endswith(".json"):
                with open(config_path, "r", encoding="utf-8") as f:
                    self._settings = json.load(f)
            else:
                raise ValueError("Поддерживаются только .json и .toml файлы")
        except Exception as e:
            raise RuntimeError(f"Ошибка загрузки конфигурации: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Возвращает значение по ключу.
        Если ключ не найден — возвращает default.
        """
        return self._settings.get(key, default)

    def reload(self) -> None:
        """
        Перезагружает конфигурацию из исходного файла.
        """
        if self._config_path is None:
            raise ValueError("Конфигурация не была загружена. Вызовите load() сначала.")
        self.load(self._config_path)  # Перезагружаем

    def set(self, key: str, value: Any) -> None:
        """
        Устанавливает значение в конфигурацию (для динамических изменений).
        Не сохраняется в файл — только в оперативную копию.
        """
        self._settings[key] = value
