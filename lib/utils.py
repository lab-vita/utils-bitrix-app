from typing import Any, Dict


def parse_nested(form_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Преобразует "плоский" словарь с ключами в стиле form-data во вложенные словари.

    Args:
        form_dict (Dict[str, Any]): Словарь с ключами строкового типа.
                                    Значения могут быть любого типа.
                                    Ключи могут содержать вложенность через квадратные скобки.

    Returns:
        Dict[str, Any]: Вложенный словарь.
    """
    result: Dict[str, Any] = {}
    for k, v in form_dict.items():
        # Разбиваем ключ на части по квадратным скобкам
        # Например: 'user[address][city]' -> ['user', 'address', 'city']
        keys = k.replace(']', '').split('[')

        # Навигация по вложенным словарям
        d: Dict[str, Any] = result
        for key in keys[:-1]:
            # Если ключа ещё нет, создаём вложенный словарь
            # Возвращаем ссылку на этот словарь для следующей итерации
            d = d.setdefault(key, {})

        # Устанавливаем значение для последнего ключа
        d[keys[-1]] = v
    return result
