from morph import morph


class Amount2Words:
    """
    Класс для преобразования денежной суммы в текстовое представление на русском языке.
    """

    def __init__(self):
        """
        Инициализация словарей числительных и форм склонений.
        """

        # Единицы (мужской род)
        self._units = [
            '',
            'один',
            'два',
            'три',
            'четыре',
            'пять',
            'шесть',
            'семь',
            'восемь',
            'девять'
        ]

        # Единицы (женский род — используется для тысяч)
        self._units_f = [
            '',
            'одна',
            'две',
            'три',
            'четыре',
            'пять',
            'шесть',
            'семь',
            'восемь',
            'девять'
        ]

        # Числа от 10 до 19
        self._teens = [
            'десять',
            'одиннадцать',
            'двенадцать',
            'тринадцать',
            'четырнадцать',
            'пятнадцать',
            'шестнадцать',
            'семнадцать',
            'восемнадцать',
            'девятнадцать'
        ]

        # Десятки
        self._tens = [
            '',
            '',
            'двадцать',
            'тридцать',
            'сорок',
            'пятьдесят',
            'шестьдесят',
            'семьдесят',
            'восемьдесят',
            'девяносто'
        ]

        # Сотни
        self._hundreds = [
            '',
            'сто',
            'двести',
            'триста',
            'четыреста',
            'пятьсот',
            'шестьсот',
            'семьсот',
            'восемьсот',
            'девятьсот'
        ]

        # Разряды (название в 3 формах + род)
        self._scales = [
            ('', '', '', 'm'),
            ('тысяча', 'тысячи', 'тысяч', 'f'),
            ('миллион', 'миллиона', 'миллионов', 'm'),
            ('миллиард', 'миллиарда', 'миллиардов', 'm'),
            ('триллион', 'триллиона', 'триллионов', 'm')
        ]

        # Формы валют
        self._currency = ('рубль', 'рубля', 'рублей')
        self._kopek = ('копейка', 'копейки', 'копеек')

    def _num_to_words(self, n, gender='m'):
        """
        Преобразует число от 1 до 999 в список слов.

        :param n: Число (0–999)
        :param gender: Род ('m' — мужской, 'f' — женский)
        :return: Список слов
        """
        if n == 0:
            return []

        words = []

        # Сотни
        if n >= 100:
            words.append(self._hundreds[n // 100])
            n %= 100

        # Десятки
        if n >= 20:
            words.append(self._tens[n // 10])
            n %= 10
        elif n >= 10:
            # Числа 10-19
            words.append(self._teens[n - 10])
            n = 0  # Обнуляем, так как единицы уже учтены

        # Единицы
        if n > 0:
            if gender == 'f':
                words.append(self._units_f[n])
            else:
                words.append(self._units[n])

        return words

    def convert(self, amount):
        """
        Преобразует денежную сумму в строку прописью.

        :param amount: Сумма (float, int или строка)
        :return: Строка с суммой прописью
        """

        # Округляем до 2 знаков после запятой
        amount = round(float(amount), 2)

        # Выделяем рубли и копейки
        rubles = int(amount)
        kopeks = int(round((amount - rubles) * 100))

        # Если рублей 0
        if rubles == 0:
            rubles_words = ['ноль']
        else:
            rubles_words = []
            parts = []
            temp = rubles

            # Разбиваем число на группы по 3 цифры
            while temp > 0:
                parts.append(temp % 1000)
                temp //= 1000

            # Обрабатываем каждую группу (тысячи, миллионы и т.д.)
            for i, part in enumerate(parts):
                if part == 0:
                    continue

                scale_index = i

                # Определяем род (тысяча — женский род)
                if scale_index == 1:
                    gender = 'f'
                else:
                    gender = 'm'

                # Преобразуем число в слова
                chunk_words = self._num_to_words(part, gender)

                # Добавляем название разряда
                if scale_index > 0:
                    scale_word = morph(part, self._scales[scale_index])
                    chunk_words.append(scale_word)

                rubles_words = chunk_words + rubles_words

        # Формируем итоговую строку
        result = ' '.join(rubles_words).strip()
        # Добавляем валюту (рубли)
        result += ' ' + morph(rubles, self._currency)
        # Добавляем копейки
        result += f' {kopeks:02d} {morph(kopeks, self._kopek)}'

        return result.capitalize()
