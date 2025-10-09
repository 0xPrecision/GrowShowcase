# # syntax=docker/dockerfile:1
# FROM python:3.12-slim
#
# # Системные зависимости по минимуму
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential curl && \
#     rm -rf /var/lib/apt/lists/*
#
# WORKDIR /app
#
# # Зависимости
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
#
# # Код
# COPY . .
#
# # Директория для данных (sqlite и т.п.)
# VOLUME ["/app/data"]
#
# # По умолчанию ничего не запускаем. Команды задаём в docker-compose.

# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# код
COPY . .

# если и только если ты реально используешь SQLite:
# VOLUME ["/app/data"]

# Запуск FastAPI (Render подставляет порт, но мы фиксируем 8000)
CMD ["uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8000"]


