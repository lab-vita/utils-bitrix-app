import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from lib.utils import parse_nested
from lib.bitrix24_client import Bitrix24Client

load_dotenv()

CLIENT_ID = os.getenv("BITRIX24_CLIENT_ID")
CLIENT_SECRET = os.getenv("BITRIX24_CLIENT_SECRET")
ENV = os.getenv("ENV")
PORT = int(os.getenv("PORT"))

app = Flask(__name__)
bx_client = Bitrix24Client(CLIENT_ID, CLIENT_SECRET)


def setup_logger():
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    if ENV != "PRODUCTION":
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s — %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logger()


@app.route("/install", methods=["POST"])
def install():
    """
    Endpoint для обработки установки приложения Bitrix24
    """

    try:
        # Bitrix присылает вложенные ключи — приводим к нормальной структуре
        data = parse_nested(request.form.to_dict())
    except Exception as error:
        logger.error(f"Ошибка парсинга form-data: {error}")
        return jsonify({"error": "bad_request"}), 400

    # Проверяем тип события
    event = data.get("event")
    if event != "ONAPPINSTALL":
        logger.warning(f"Неожиданное событие: {event}")
        return jsonify({"error": "unexpected_event", "event": event}), 400

    auth_data = data.get("auth", {})
    if not auth_data:
        logger.error("Отсутствуют auth данные")
        return jsonify({"error": "missing_auth"}), 400

    # Сохраняем токены Bitrix24
    bx_client.set_tokens(auth_data)

    logger.info(f"Приложение установлено. Портал: {auth_data.get('domain')}")
    return "", 200


if __name__ == "__main__":
    logger.info(f"Запуск сервера в среде: {ENV}")
    app.run(host="0.0.0.0", port=PORT, debug=(ENV != "PRODUCTION"))
