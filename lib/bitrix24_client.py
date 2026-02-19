import json
import time
from pathlib import Path
from typing import Any, Dict


class Bitrix24Client:
    """
    Клиент для работы с Bitrix24
    """

    # URL OAuth-сервера Bitrix24 для получения и обновления токенов
    OAUTH_URL = "https://oauth.bitrix24.tech/oauth/token/"

    def __init__(self, client_id: str, client_secret: str, tokens_file: str = 'utils_bitrix_app_tokens.json'):
        """
        Инициализация клиента.

        :param client_id: OAuth client_id приложения Bitrix24
        :param client_secret: OAuth client_secret приложения Bitrix24
        :param tokens_file: Путь к JSON-файлу для хранения токенов
        """

        self.client_id = client_id
        self.client_secret = client_secret
        self.settings_file = Path(tokens_file)
        self._tokens: Dict[str, Any] = self._load_tokens()

    def _load_tokens(self) -> Dict[str, Any]:
        """
        Загружает токены из файла.

        :return: Словарь с токенами или пустой словарь, если файл отсутствует или повреждён
        """

        if not self.settings_file.exists():
            return {}

        try:
            with self.settings_file.open(encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_tokens(self):
        """
        Сохраняет текущие токены в JSON-файл. Файл перезаписывается полностью.
        """

        with self.settings_file.open("w", encoding="utf-8") as file:
            json.dump(self._tokens, file, indent=4)

    def set_tokens(self, auth_data: Dict[str, Any]):
        """
        Обновляет токены новыми данными авторизации.
        """

        # Список ключей, которые нужно сохранить
        needed_keys = ["access_token", "refresh_token", "client_endpoint", "expires"]

        # Фильтруем входящий словарь, оставляя только нужные ключи
        filtered_data = {key: auth_data.get(key) for key in needed_keys}

        self._tokens.update(filtered_data)
        self._save_tokens()
