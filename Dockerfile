# Указываем базовый образ Python
FROM python:3.9-slim

# Устанавливаем необходимые системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
RUN pip install poetry

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл pyproject.toml и poetry.lock
COPY pyproject.toml poetry.lock* /app/

# Устанавливаем зависимости с помощью Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# Копируем весь код проекта в контейнер
COPY src /app/src

COPY src/alembic.ini /app/

COPY src/alembic /app/alembic

ENV PYTHONPATH="${PYTHONPATH}:/app/src"

# Указываем команду для запуска вашего приложения
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]