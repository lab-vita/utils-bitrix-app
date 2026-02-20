import os
import logging
from flask import Flask, request, jsonify
from http import HTTPStatus
from dotenv import load_dotenv

from lib.utils import parse_nested
from lib.bitrix24_client import Bitrix24Client

load_dotenv()

CLIENT_ID = os.environ.get("BITRIX24_CLIENT_ID")
CLIENT_SECRET = os.environ.get("BITRIX24_CLIENT_SECRET")
ENV = os.environ.get("ENV")
PORT = int(os.environ.get("PORT"))
APP_URL = os.environ.get("APP_URL")

app = Flask(__name__)
bx_client = Bitrix24Client(CLIENT_ID, CLIENT_SECRET)


def build_logger() -> logging.Logger:
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.DEBUG if ENV != "PRODUCTION" else logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)-8s %(name)s — %(message)s")
    )
    app_logger.addHandler(handler)
    return app_logger


logger = build_logger()


def register_activity():
    """
    Регистрирует активити Сумма прописью в бизнес-процессах Bitrix24
    """

    bx_client.call("bizproc.activity.add", {
        "CODE": "utils-bitrix-app.amount2words",
        "HANDLER": f"{APP_URL}/amount2words-handler",
        "USE_SUBSCRIPTION": "Y",
        "NAME": "Сумма прописью",
        "DESCRIPTION": "Преобразует число в текстовое представление суммы",
        "PROPERTIES": {
            "SOURCE_AMOUNT": {
                "NAME": "Исходная сумма",
                "DESCRIPTION": "Укажите код поля с исходной суммой (UF_CRM_***)",
                "TYPE": "string",
                "REQUIRED": "Y",
                "MULTIPLE": "N",
                "DEFAULT": ""
            },
            "RESULT": {
                "NAME": "Сумма прописью",
                "DESCRIPTION": "Укажите код поля для суммы прописью (UF_CRM_***)",
                "TYPE": "string",
                "REQUIRED": "Y",
                "MULTIPLE": "N",
                "DEFAULT": ""
            }
        },
        "RETURN_PROPERTIES": {
            "STATUS": {
                'NAME': 'Статус операции',
                'TYPE': 'string'
            }
        }
    })

    @app.route("/install", methods=["POST"])
    def install():
        """
        Endpoint для обработки установки приложения Bitrix24
        """

        try:
            # Bitrix присылает вложенные ключи — приводим к нормальной структуре
            data = parse_nested(request.form.to_dict())
        except Exception as error:
            logger.exception("Ошибка парсинга form-data при установке: %s", error)
            return jsonify({"error": "bad_request"}), HTTPStatus.BAD_REQUEST

        # Проверяем тип события
        if (event := data.get("event")) != "ONAPPINSTALL":
            logger.warning("Неожиданное событие: %s", event)
            return jsonify({"error": "unexpected_event", "event": event}), HTTPStatus.BAD_REQUEST

        auth_data = data.get("auth") or {}
        if not auth_data:
            logger.error("Отсутствуют auth-данные в запросе установки")
            return jsonify({"error": "missing_auth"}), HTTPStatus.BAD_REQUEST

        # Сохраняем токены Bitrix24
        bx_client.set_tokens(auth_data)
        logger.info("Токены сохранены. Портал: %s", auth_data.get("domain"))

        return "", HTTPStatus.OK

    if __name__ == "__main__":
        logger.info(f"Запуск сервера в среде: {ENV}")
        app.run(host="0.0.0.0", port=PORT, debug=(ENV != "PRODUCTION"))
