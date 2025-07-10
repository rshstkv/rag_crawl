FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
RUN pip install poetry

# Копируем файлы конфигурации Poetry
COPY pyproject.toml poetry.lock ./

# Настраиваем Poetry
RUN poetry config virtualenvs.create false

# Устанавливаем зависимости
RUN poetry install --only=main --no-root

# Копируем исходный код
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Создаем директорию для логов
RUN mkdir -p logs

# Устанавливаем PYTHONPATH
ENV PYTHONPATH=/app/src

# Открываем порт
EXPOSE 8000

# Запускаем приложение
CMD ["python", "-m", "rag_crawl.main"] 