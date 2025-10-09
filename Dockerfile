# syntax=docker/dockerfile:1.6
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Базовые системные зависимости (сборка колёс, healthcheck curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копируем проект
COPY . .

# Каталог для данных (SQLite, миграции и т.д.)
RUN mkdir -p /data && chown -R root:root /data

# Значения по умолчанию: SQLite в общем volume /data
ENV DATABASE_URL=sqlite:///data/shop.db

# Порт приложения (web-сервис будет слушать 8000)
EXPOSE 8000

# Универсальный ENTRYPOINT; команду задаём в docker-compose
ENTRYPOINT ["/bin/bash","-lc"]




