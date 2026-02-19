def morph(n, forms):
    """
    Определяет правильную форму слова в зависимости от числа.

    :param n: Число
    :param forms: Кортеж из трех форм (1, 2-4, 5+)
    :return: Корректная форма слова
    """

    n = abs(n) % 100

    if 10 < n < 20:
        return forms[2]

    n = n % 10

    if n == 1:
        return forms[0]
    if 1 < n < 5:
        return forms[1]
    return forms[2]
