# Используем официальный облегчённый образ Python 3.13
FROM python:3.13-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем только файл зависимостей, чтобы Docker мог кешировать установку
COPY requirements.txt .

# Устанавливаем зависимости Python без кеша и без проверки версии pip
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

# Копируем весь проект в рабочую директорию
COPY . .

# Создаём системную группу и пользователя "app" для безопасности
RUN groupadd --system app && useradd --system --gid app --no-create-home app

# Передаём права на директорию /app пользователю "app"
RUN chown -R app:app /app

# Переключаемся на пользователя "app" для запуска приложения (не root!)
USER app

# Создаём точку монтирования для хранения данных вне контейнера
VOLUME ["/app/data"]

# Команда по умолчанию для запуска приложения
CMD ["python", "main.py"]
