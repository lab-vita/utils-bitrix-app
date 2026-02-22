import os
import logging
from flask import Flask, request, jsonify
from http import HTTPStatus
from dotenv import load_dotenv

from lib.utils import parse_nested
from lib.bitrix24_client import Bitrix24Client
from amount2words.amount2words import Amount2Words

load_dotenv()

CLIENT_ID = os.environ.get("BITRIX24_CLIENT_ID")
CLIENT_SECRET = os.environ.get("BITRIX24_CLIENT_SECRET")
ENV = os.environ.get("ENV")
PORT = int(os.environ.get("PORT"))
APP_URL = os.environ.get("APP_URL")

app = Flask(__name__)
bx_client = Bitrix24Client(CLIENT_ID, CLIENT_SECRET)
converter = Amount2Words()


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

    try:
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
                "ERROR": {
                    "NAME": "Ошибка",
                    "TYPE": "string",
                },
                "STATUS": {
                    "NAME": "Статус операции",
                    "TYPE": "string"
                }
            }
        })
    except Exception as exc:
        # Активити уже зарегистрирована — нормальная ситуация при переустановке
        if "ERROR_ACTIVITY_ALREADY_INSTALLED" in str(exc):
            logger.info("Активити 'Сумма прописью' уже зарегистрирована, пропускаем")
            return
        raise


def send_bizproc_event(event_token: str, error_msg: str = "", status_msg: str = "ok"):
    """
    Завершает активити бизнес-процесса через bizproc.event.send
    """

    try:
        bx_client.call("bizproc.event.send", {
            "event_token": event_token,
            "return_values": {"ERROR": error_msg, "STATUS": status_msg},
        })
    except Exception as error:
        logger.exception("Ошибка API при отправке bizproc.event.send:", error)


def update_crm_field(deal_id: str, field: str, value: str):
    """
    Обновляет поле CRM-сущности
    """

    try:
        bx_client.call("crm.deal.update", {
            "id": deal_id,
            "fields": {
                field: value
            }
        })

        logger.info("Поле %s обновлено: → %s", field, value)
    except Exception as error:
        logger.exception("Ошибка API при обновлении: %s", error)


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

    try:
        register_activity()
        logger.info("Активити 'amount2words' успешно зарегистрирована")
    except Exception as error:
        logger.exception("Ошибка регистрации активити: %s", error)

    return "", HTTPStatus.OK


@app.route("/amount2words-handler", methods=["POST"])
def amount2words_handler():
    """
    Обработчик активити Сумма прописью бизнес-процесса
    """

    try:
        data = parse_nested(request.form.to_dict())
    except Exception as error:
        logger.exception("Ошибка парсинга form-data в обработчике активити: %s", error)
        return jsonify({"error": "bad_request"}), HTTPStatus.BAD_REQUEST

    event_token = data.get("event_token")
    if not event_token:
        logger.error("Отсутствует event_token — невозможно завершить активити")
        return jsonify({"error": "missing_event_token"}), HTTPStatus.BAD_REQUEST

    properties = data.get("properties") or {}
    source_amount = properties.get("SOURCE_AMOUNT")

    if source_amount == "":
        source_amount = "0"
    else:
        source_amount = str(source_amount).split("|")[0]

    try:
        amount_in_words = converter.convert(source_amount)
        logger.info("Конвертация: %s → %s", source_amount, amount_in_words)
    except Exception as error:
        logger.exception("Ошибка конвертации суммы '%s': %s", source_amount, error)
        send_bizproc_event(event_token, error_msg="Ошибка конвертации суммы", status_msg="error")
        return "", HTTPStatus.OK

    result_field = properties.get("RESULT")
    document_id = data.get("document_id")
    deal_raw = document_id.get("2")

    if deal_raw.startswith("DEAL_"):
        deal_id = deal_raw.split("_")[1]
    else:
        deal_id = None

    try:
        update_crm_field(deal_id, result_field, amount_in_words)
        send_bizproc_event(event_token, error_msg="", status_msg="ok")
    except Exception as error:
        logger.exception("Ошибка обновления поля суммы: %s", error)
        send_bizproc_event(event_token, error_msg="Ошибка обновления поля суммы", status_msg="error")
        return "", HTTPStatus.OK

    return "", HTTPStatus.OK


if __name__ == "__main__":
    logger.info(f"Запуск сервера в среде: {ENV}")
    app.run(host="0.0.0.0", port=PORT, debug=(ENV != "PRODUCTION"))
