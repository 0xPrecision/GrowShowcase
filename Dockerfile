# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Системные зависимости по минимуму
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код
COPY src ./src

# Директория для данных (sqlite и т.п.)
VOLUME ["/data"]

# По умолчанию ничего не запускаем. Команды задаём в docker-compose.

