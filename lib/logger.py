import logging


def build_logger(env: str) -> logging.Logger:
    """
    Создаёт и настраивает логгер приложения.

    :param env: Текущее окружение ('PRODUCTION', 'DEVELOPMENT' и т.д.)
    :return: Настроенный логгер
    """

    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.DEBUG if env != "PRODUCTION" else logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)-8s %(name)s — %(message)s")
    )
    app_logger.addHandler(handler)
    return app_logger
